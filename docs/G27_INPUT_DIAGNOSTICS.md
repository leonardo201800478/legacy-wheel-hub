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
