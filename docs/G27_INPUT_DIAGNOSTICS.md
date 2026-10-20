# Diagnóstico de entradas do Logitech G27 / DFGT

A ferramenta coleta evidências para mapear os eixos que o Windows expõe via SDL/Pygame, registrar pedais e botões e comparar os valores encontrados no XML do Logitech Gaming Software (LGS).

## Escopo e limitações

- Somente leitura: não altera registro, driver, firmware, configurações do volante ou XML do LGS.
- Enumera joysticks e registra eixos, botões e hats em CSV com timestamp.
- A calibração guiada tenta identificar qual eixo varia ao pressionar cada pedal e registra direção e amplitude.
- Opcionalmente lê XMLs LGS correspondentes ao executável informado e reporta Axis e Sign.
- Os valores coletados são os expostos pela API SDL/Pygame, não pacotes USB HID brutos.
- Encontrar Sign=-1 no XML não comprova que o perfil está ativo nem que o driver aplicou a alteração. O LGS pode selecionar perfil por executável; confirme o perfil ativo no cenário medido.
- A numeração SDL dos eixos não é necessariamente equivalente aos nomes de eixo no XML LGS, como R e Z.

## Requisitos

Windows 10/11 e Python 3.10+ recomendado. Instale:

~~~powershell
py -m pip install pygame-ce
~~~

Não é necessário executar como administrador.

## Uso

Na raiz do repositório:

~~~powershell
py tools\g27_input_diagnostics.py
~~~

Selecione um dispositivo específico quando houver mais de um:

~~~powershell
py tools\g27_input_diagnostics.py --device 0
~~~

Inspecione também os XMLs LGS de um executável:

~~~powershell
py tools\g27_input_diagnostics.py --exe "mame.exe"
~~~

Pule a calibração e comece a registrar:

~~~powershell
py tools\g27_input_diagnostics.py --skip-calibration --interval 0.01
~~~

Arquivos gerados por padrão em .\g27-diagnostics\:

- g27_input_<data>.csv: amostras de todos os eixos, botões e hats.
- g27_report_<data>.json: dispositivo, GUID, calibração, XML LGS encontrado e observações.

## Protocolo recomendado

1. Feche jogos e outros programas que possam interferir na entrada.
2. Execute a ferramenta e confirme nome e GUID do G27.
3. Durante a calibração, deixe os outros pedais soltos e pressione apenas o pedal solicitado.
4. Repita a calibração após inverter o pedal no Legacy Wheel Hub/LGS.
5. Compare os relatórios antes/depois: eixo alterado, direção, amplitude e estabilidade.
6. Para validar um perfil por jogo, confirme que o LGS realmente ativou o perfil desse executável. Não conclua que funcionou apenas porque o XML contém o valor esperado.
7. Revise CSV e JSON antes de compartilhar: GUIDs e caminhos locais podem revelar detalhes do computador.

## Interpretação

- Variação próxima de 1.0 costuma indicar grande movimento do eixo. Variação baixa pode significar que o pedal não foi movimentado, que outro eixo foi lido ou que a API não expõe o pedal como esperado.
- A direção registrada descreve o movimento observado; não declara, isoladamente, que o eixo está correto ou invertido.
- Se dois pedais movimentarem o mesmo eixo, repita o teste isoladamente e investigue o modo combinado de pedais/driver.

## Próxima etapa

Se SDL/Pygame não fornecer evidências suficientes, adicionar instrumentação Windows dedicada para enumerar dispositivos e eixos DirectInput, ler Raw Input/HID quando compatível e comparar entrada observada com Sign no perfil LGS. Essa etapa deve ser orientada pelos logs reais, sem presumir que índices SDL correspondam aos eixos LGS.


## Registro preliminar de calibração (relato do usuário, 2026-10-20)

Primeira execução reportada para o G27:

| Pedal | Eixo SDL (numeração exibida, iniciada em 1) | Variação | Direção observada |
|---|---:|---:|---|
| Acelerador | 2 | 2.000 | decreasing |
| Freio | 3 | 2.000 | decreasing |
| Embreagem | 5 | 2.000 | decreasing |

A amplitude 2.000 é compatível com uma excursão aproximada de +1 a -1 no eixo normalizado. Os três pedais foram detectados em eixos SDL distintos, todos decrescentes durante a pressão. Isso ainda não confirma que a inversão de um perfil LGS foi aplicada pelo driver, nem mapeia diretamente os eixos SDL aos nomes `R`/`Z` do XML.

A amostra final reportada foi `[-0.12796, 0.21429, 0.99997, -0.4679, 0.99997]`. Como ela é apenas um instante e não há informação sobre a posição de cada pedal nesse instante, não deve ser usada para concluir se os pedais estavam em repouso ou invertidos. O próximo passo é examinar o JSON completo (principalmente baseline, minimum e maximum de cada pedal) e o CSV, além do XML LGS correspondente ao executável testado. Este registro é evidência de uma execução reportada, não um teste independente reproduzido pelos mantenedores.


## Coleta avançada: relatórios HID do Windows Raw Input

Foi adicionada a ferramenta `tools/g27_windows_raw_input_diagnostics.py`, separada do leitor SDL. Ela enumera dispositivos Raw Input visíveis ao Windows e tenta registrar relatórios de coleções HID Generic Desktop com uso Joystick (`0x01/0x04`) e Game Pad (`0x01/0x05`). Os relatórios são gravados como bytes hexadecimais, com timestamp, identificador do dispositivo, caminho, tamanho e índice do relatório.

Execute em um terminal normal, na raiz do repositório:

~~~powershell
py tools\g27_windows_raw_input_diagnostics.py
~~~

Para uma captura de 120 segundos:

~~~powershell
py tools\g27_windows_raw_input_diagnostics.py --seconds 120
~~~

Para capturar somente quando a janela da ferramenta estiver em primeiro plano:

~~~powershell
py tools\g27_windows_raw_input_diagnostics.py --foreground-only
~~~

Arquivos de saída:

- `g27-diagnostics/g27_raw_hid_<data>.csv`: um registro por relatório HID observado.
- `g27-diagnostics/g27_raw_hid_<data>.json`: inventário inicial, dispositivos observados, coleções registradas, contagem, erros e limitações.

Durante a captura, gire o volante lentamente de batente a batente, mantenha-o parado no centro, pressione cada pedal separadamente e acione todos os botões, direcional e controles auxiliares. Para melhorar a comparação, faça uma sequência por vez e anote o horário aproximado de cada ação.

### Limitações importantes

- Raw Input não é um sniffer elétrico do barramento USB. Ele registra relatórios HID entregues ao processo pelo Windows.
- Os bytes ainda não são interpretados como eixos, botões ou comandos. A próxima etapa é obter e analisar o descritor HID e correlacionar os campos com os relatórios.
- O G27 pode expor mais de uma coleção HID ou usar caminhos que não correspondam às duas coleções registradas. Uma captura vazia não prova ausência de atividade; nesse caso, devemos ampliar a enumeração/abordagem.
- Esta ferramenta não lê nem altera relatórios de saída, não envia comandos FFB e não altera Registro, drivers ou configurações do LGS.
- O uso de Raw Input é registrado apenas para o processo de diagnóstico. Feche a ferramenta ao terminar; ela remove seus registros de Raw Input ao encerrar.

### Coleta comparativa recomendada

1. Capture Raw Input e SDL/Pygame separadamente, com o mesmo volante conectado.
2. Faça o primeiro conjunto sem tocar nos controles, para registrar ruído/estado em repouso.
3. Gire o volante e acione cada pedal individualmente, aguardando entre movimentos.
4. Acione cada botão uma vez, incluindo os botões de mudança de marcha e o direcional.
5. Repita depois de alterar uma única opção no LGS ou no Hub.
6. Compare os relatórios e guarde o JSON/CSV de cada cenário. Não conclua que o perfil está ativo só por encontrar um XML.

Não compartilhe os arquivos sem revisar caminhos locais e identificadores do dispositivo.


## Análise das capturas enviadas ao repositório (2026-10-20)

Arquivos analisados:
- `g27-diagnostics/g27_report_20261020_094107.json` e CSV correspondente.
- `g27-diagnostics/g27_report_20261020_094858.json` e CSV correspondente.
- `g27-diagnostics/g27_raw_hid_20261020_094750.json` e CSV correspondente.

### Resultados SDL

| Captura | Amostras | Duração aproximada | Taxa efetiva calculada |
|---|---:|---:|---:|
| Com calibração | 4.377 | 89,57 s | 48,9 amostras/s |
| Sem calibração | 8.313 | 87,21 s | 95,3 amostras/s |

A taxa efetiva é calculada a partir das linhas e do tempo decorrido; não deve ser tratada como frequência USB do volante.

Na primeira captura, os eixos SDL 2, 3 e 5 percorreram de `-1` a aproximadamente `+1`, com mudanças observadas durante a calibração. O relatório associa esses eixos ao acelerador, freio e embreagem, respectivamente, e classifica a confiança como forte. O eixo 1 permaneceu em `-0.12796` nessa captura; o eixo 4 permaneceu em `-0.4679`. O valor inicial de eixo 5 no CSV (`-1`) não coincide com o baseline de eixo 5 no JSON (`+0.99997`), portanto o JSON não deve ser usado sozinho para reconstruir a sequência temporal completa dessa captura.

Na segunda captura, todos os cinco eixos variaram ao menos uma vez; os eixos 1, 2, 3 e 5 atingiram aproximadamente `-1` e `+1`. O eixo 4 começou em `0` e passou uma vez a `-0.4679`, permanecendo estável pelo restante da gravação. Esse comportamento pode ser estado inicial da API ou um eixo não ativo, mas a captura não permite decidir qual hipótese é correta. Todos os 23 botões apresentaram pelo menos algumas amostras ativas; o hat registrou valores direcionais em X e Y.

### Resultados Raw Input

O JSON reporta 7.359 relatórios em aproximadamente 41,05 segundos (cerca de 179 relatórios/s agregados). O inventário inclui o caminho HID `VID_046D&PID_C29B`, compatível com a identificação esperada para o G27. Entretanto, a captura registrou coleções de vários dispositivos HID e o relatório não permite atribuir todos os 7.359 relatórios ao G27 sem agrupar o CSV por `device_path`.

**Problema de qualidade de dados identificado:** apesar de os caminhos conterem VID/PID, os campos `vendor_id`, `product_id`, `usage_page` e `usage` foram gravados como zero para os dispositivos HID. A leitura da estrutura `RIDI_DEVICE_INFO` precisa ser corrigida/verificada antes de confiar nesses campos. A enumeração por caminho de dispositivo ainda fornece pistas, mas não substitui o descritor HID nem a decodificação dos relatórios.

### Conclusões e próximos passos

1. A SDL vê o volante como `G27 Racing Wheel`, GUID `0300be956d0400009bc2000000000000`, com 5 eixos, 23 botões e 1 hat.
2. A correspondência provisória mais forte é: eixo SDL 1 = direção; eixos 2, 3 e 5 = pedais conforme a calibração guiada; eixo 4 = não identificado.
3. As capturas não demonstram que uma inversão LGS esteja ativa nem identificam como o LGS envia configurações ao driver.
4. Corrigir os metadados Raw Input e adicionar resumo por dispositivo/caminho e tamanho de relatório.
5. Decodificar o descritor HID e correlacionar os bytes do G27 com os movimentos controlados; depois comparar a mesma ação antes/depois de uma única mudança de perfil.

Estes resultados foram calculados a partir dos arquivos enviados ao repositório; não representam uma execução independente no equipamento.


### Correção da coleta Raw Input após análise

A análise do JSON revelou que a chamada de metadados `RIDI_DEVICEINFO` não estava sendo validada corretamente: as funções Win32 não tinham assinaturas `ctypes` explícitas, e o retorno padrão assinado podia fazer a comparação com o sentinela de erro `UINT(-1)` falhar. A ferramenta foi atualizada para declarar os tipos de retorno/argumentos e resumir o número de relatórios e os tamanhos por dispositivo no JSON.

**A correção ainda precisa ser validada no Windows do usuário.** Faça uma nova captura após atualizar o script; confira se os campos VID/PID/Usage deixam de aparecer como zero e se o JSON traz `report_summary_by_device`. O resumo permitirá distinguir os relatórios do caminho do G27 dos relatórios de outros dispositivos que também estejam conectados.


## Capturas Raw Input posteriores à correção (2026-10-20)

Foram analisadas duas novas capturas de aproximadamente 60 segundos. O script agrupou 4.058 e 4.108 relatórios, respectivamente, no caminho HID que contém `VID_046D&PID_C29B`; todos os relatórios tinham 13 bytes e não foram reportados erros. Vários bytes variam, mas ainda não podem ser associados a eixos ou botões sem interpretar o descritor HID.

O relatório detalhado e as limitações estão em [Análise das capturas Raw Input do G27 — 2026-10-20](G27_RAW_INPUT_CAPTURE_20261020.md). Próxima etapa: recuperar o descritor HID e decodificar os campos antes de tentar identificar os bytes de cada eixo/pedal.


## Teste funcional da inversão no MAME: Legacy Wheel Hub sem efeito (2026-10-20)

O usuário esclareceu que o MAME já está configurado para receber a inversão feita pelo Logitech Gaming Software (LGS) e que esse fluxo funciona com a configuração original do LGS. Nos testes em que a alteração é feita pelo Legacy Wheel Hub, a inversão não ocorre.

**Conclusão funcional:** a alteração atual feita pelo Legacy Wheel Hub não está reproduzindo o efeito da configuração original do LGS. Deve ser tratada como implementação ineficaz, não como recurso corrigido. Não é necessário reabrir a hipótese de que o MAME esteja configurado incorretamente; o problema a investigar é a diferença entre a configuração LGS funcional e a alteração produzida pelo Hub.

### O que ainda não sabemos

- Se o XML editado pelo Hub é a fonte de configuração que o LGS realmente consome para aplicar `AxisDynamics`/inversão.
- Se o LGS normaliza, reescreve, ignora ou complementa esses campos com estado armazenado em outro local.
- Qual mecanismo interno o LGS usa para transformar a entrada entregue ao jogo.
- Em que camada a inversão funcional do LGS aparece. As capturas SDL e Raw Input disponíveis não comprovam, por si só, o valor final que o MAME recebe.

### Plano de investigação

1. Comparar um perfil original funcional exportado pelo LGS com o mesmo perfil após uma única inversão feita pela interface oficial do LGS; identificar todas as diferenças persistidas, não apenas `Sign` no XML.
2. Comparar esses artefatos com o perfil produzido pelo Legacy Wheel Hub e verificar se o Hub preserva a estrutura, os campos e a semântica esperados pelo LGS.
3. Investigar documentação e evidências reproduzíveis sobre o carregamento de perfis e o mecanismo de aplicação do LGS; não presumir que editar XML seja suficiente.
4. Projetar um teste A/B usando o mesmo executável, eixo e ação física: configuração original do LGS funcional versus configuração equivalente produzida pelo Hub.
5. Só depois de identificar a diferença, corrigir a implementação e validar no MAME. Se o LGS depender de estado ou de uma interface não representada no XML, documentar essa dependência e avaliar uma via alternativa que o MAME efetivamente consuma.

O relato do usuário estabelece o resultado funcional do teste; a causa interna ainda precisa ser investigada. Nenhuma conclusão sobre o mecanismo do driver deve ser apresentada como comprovada sem evidência adicional.


## Registro automático de diagnóstico da inversão (Legacy Wheel Hub)

Desde o commit de diagnóstico, o aplicativo registra automaticamente uma trilha local em segundo plano ao iniciar. Não é necessário abrir a ferramenta Raw Input separada nem executar comandos.

**Local padrão do log:**

```text
%LOCALAPPDATA%\Legacy Wheel Hub\diagnostics\pedal_inversion_AAAAMMDD_HHMMSS.jsonl
```

Cada inicialização gera um arquivo JSON Lines independente. O logger não altera o driver, o Registro, o perfil LGS nem a entrada do volante; ele observa o inventário HID e os relatórios que o próprio Legacy Wheel Hub já lê.

### O que é registrado

- Início/fim da sessão, versão do aplicativo, versão do Python e executável.
- Inventário HID Logitech com VID/PID, nome do fabricante/produto e metadados de interface disponíveis; caminhos HID e números de série não são incluídos.
- Perfil de hardware identificado, índices de bytes usados pelo Hub para acelerador/freio/embreagem e valor da opção interna `pedal_invert`.
- Configuração dos perfis do Hub: flags `invert_throttle`, `invert_brake`, `invert_clutch`, `driver_pedal_inversion_configured` e somente o nome do executável associado.
- Relatórios de entrada que mudam, limitados a aproximadamente 20 amostras por segundo, com bytes brutos em hexadecimal e os valores de direção/pedais calculados pelo Hub.
- Conexões, desconexões detectadas, erros de abertura/leitura HID e mudanças de perfil de jogo observadas pelo aplicativo.

### Como usar para investigar os pedais

1. Abra o Legacy Wheel Hub normalmente e deixe-o conectado ao G27.
2. Sem mudar outras configurações, mova a direção e pressione separadamente acelerador, freio e embreagem, primeiro em repouso e depois até o fim do curso.
3. Feche o aplicativo normalmente para registrar o fim da sessão.
4. Abra o arquivo mais recente na pasta indicada e compare eventos `input_sample`: `raw_report_hex`/ `raw_bytes` mostram o relatório lido pelo Hub; `throttle_value`, `brake_value` e `clutch_value` mostram os valores após a interpretação atual do Hub.
5. Compare uma sessão com a configuração original funcional do LGS e outra com a alteração do Legacy Wheel Hub, alterando uma única variável por vez.

### Limites importantes

- Este log mostra a entrada HID que o Legacy Wheel Hub lê e como o próprio Hub a interpreta. **Não mostra diretamente o valor final recebido pelo MAME** nem prova que o LGS aplicou uma transformação.
- O logger não captura teclas, conteúdo de outros aplicativos, tráfego de rede ou relatórios HID de saída/FFB.
- O registro é automático e local. Antes de compartilhar, revise o arquivo. Ele contém amostras de entrada do volante e nomes de perfis/executáveis, embora não grave caminhos completos nem números de série.
- Se o arquivo não for criado, verifique permissões de gravação em `%LOCALAPPDATA%\Legacy Wheel Hub\diagnostics`. Falhas de diagnóstico são tratadas para não impedir a inicialização do aplicativo.

