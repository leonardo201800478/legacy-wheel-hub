# Logitech G27 no Windows: arquitetura de drivers, LGS e oportunidades para o Legacy Wheel Hub

**Status:** nota técnica de pesquisa; separa fatos documentados, inferências e hipóteses a validar experimentalmente.  
**Escopo:** Windows 10/11, Logitech G27 / Driving Force GT, Logitech Gaming Software (LGS), DirectInput, USB HID e Legacy Wheel Hub.

## Resumo executivo

O caminho mais seguro para evoluir o Legacy Wheel Hub é tratar o volante como uma pilha de camadas, e não como um único “driver Logitech”:

1. **Dispositivo e transporte USB**: o firmware do volante envia relatórios de entrada e recebe comandos/relatórios compatíveis com o dispositivo.
2. **Pilha HID do Windows**: para dispositivos HID, o Windows usa o driver de classe `hidclass.sys` e o driver de transporte apropriado. Aplicações podem enumerar coleções HID e ler/escrever relatórios por APIs documentadas.
3. **Interface de controle de jogos**: aplicações podem consumir o dispositivo por DirectInput, inclusive eixos, botões e efeitos de force feedback (FFB). O caminho exato e as extensões específicas utilizadas pelo G27 dependem do driver instalado.
4. **Software Logitech (LGS)**: gerencia perfis por aplicação e oferece ajustes e funções específicas do volante. Um perfil XML descreve dados/configuração do perfil; não prova, por si só, qual protocolo ou chamada interna o LGS usa para programar o driver.
5. **Jogo e middleware**: o jogo pode ler eixos via DirectInput/Raw Input ou outra API e enviar efeitos FFB por uma interface compatível. Alguns jogos também têm sua própria configuração de inversão/curva.

**Consequência prática:** antes de alterar o driver de kernel, devemos descobrir quais parâmetros são configurados por registro, quais são enviados por API/IOCTL/relatórios HID e quais são aplicados pelo LGS ou pelo jogo. Implementar a mesma configuração em camadas diferentes pode duplicar transformações ou gerar incompatibilidade.

## Arquitetura documentada

### 1. HID no Windows

A documentação da Microsoft descreve `hidclass.sys` como o driver de classe HID, que faz a ponte entre clientes HID e os transportes. O driver de transporte e a classe HID criam a pilha do dispositivo; coleções HID podem ser acessadas por clientes de modo usuário ou kernel. Aplicações podem usar as rotinas `HidD_*` e `HidP_*`, enquanto operações de baixo nível usam IOCTLs HID documentados.

Referências:
- [Microsoft Learn — HID architecture](https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-architecture)
- [Microsoft Learn — HID client drivers](https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-client-drivers)
- [Microsoft Learn — HID API / IOCTLs](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/_hid/)

**O que isso significa para o projeto**
- Enumerar e identificar o G27 por VID/PID, interface, coleção e caminho de dispositivo, em vez de depender apenas de um nome amigável.
- Registrar o descritor HID e os relatórios observados no equipamento real; não presumir que todos os relatórios ou interfaces sejam iguais entre versões de driver.
- Manter a leitura de eixos separada do canal de configuração/FFB. A existência de uma coleção HID não demonstra que toda a funcionalidade do volante esteja exposta como HID genérico.
- Não escrever relatórios HID arbitrários: comandos desconhecidos podem não ter efeito ou deixar o dispositivo em estado inesperado.

### 2. DirectInput e force feedback

A Logitech publica um [SDK para volantes](https://www.logitechg.com/pt-br/programs/developer-alliance), que descreve suporte a efeitos FFB predefinidos ou personalizados e encapsula controles DirectInput. Isso confirma que DirectInput é uma interface relevante para a integração com jogos e software para volantes Logitech, mas não documenta o protocolo privado completo entre LGS e cada versão do driver G27.

Referências:
- [Logitech G — Developer Alliance / Wheel SDK](https://www.logitechg.com/pt-br/programs/developer-alliance)
- [Microsoft Learn — HID (interfaces e IOCTLs)](https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/)

**Implicações**
- Distinguir **entrada** (eixos/pedais/botões), **configuração** (faixa de rotação, sensibilidade, força) e **saída FFB** (efeitos enviados pelo jogo).
- Para compatibilidade, preferir APIs públicas de entrada/FFB quando elas atendem ao requisito; reservar acesso HID direto para recursos que tenham sido identificados e testados.
- O fato de um jogo receber eixos corretos não prova que os ajustes de rotação, mola, amortecimento ou FFB estejam configurados corretamente. São caminhos relacionados, mas não equivalentes.

### 3. LGS, perfis XML e parâmetros por jogo

Perfis LGS podem conter configurações por aplicativo e opções que o software aplica quando detecta um executável. O XML é evidência do **formato de configuração**, não prova isolada do mecanismo de execução. Para determinar como uma opção chega ao driver, é preciso observar o comportamento do software e correlacionar as alterações com chamadas de API, valores de registro, IOCTLs e relatórios USB/HID.

**Hipótese a testar — eixos invertidos:** se um perfil XML produz pedais invertidos em um jogo, há pelo menos três possibilidades:
- o LGS transforma ou remapeia o eixo antes de o jogo lê-lo;
- o LGS altera uma configuração persistente consumida pelo driver;
- o perfil ativa uma opção ou modo que o jogo interpreta de maneira diferente.

Não devemos afirmar que a inversão ocorre no kernel sem evidência. O experimento mais informativo compara o mesmo eixo em (a) painel de controle do Windows, (b) monitor do Legacy Wheel Hub, (c) jogo com LGS ativo e perfil carregado, e (d) jogo sem LGS/perfil, mantendo o mesmo driver.

### 4. Drivers legados e compatibilidade

O README do Legacy Wheel Hub indica que o projeto conversa com o volante por USB HID e com configurações do driver via Registro. A página comunitária [Legacy Logitech wheels for Windows 11](https://github.com/Mysli0210/Legacy-Logitech-wheels-for-W11) é uma referência útil para instalação/compatibilidade, mas deve ser tratada como fonte comunitária, não como especificação oficial da Logitech ou da Microsoft.

Não se deve remover filtros, desativar Integridade da Memória ou alterar políticas de segurança como primeira solução. Primeiro, identificar o pacote INF, serviços e filtros realmente associados ao dispositivo e testar em uma configuração reversível.

## Plano de investigação reproduzível

### Fase A — inventário, sem alterações

1. Registrar versão do Windows, versão do LGS, versão do driver e pacote INF ativo.
2. Capturar VID/PID, caminho de dispositivo, interfaces/coleções, descritor HID e IDs de hardware/compatíveis.
3. Guardar cópia/exportação das chaves de Registro relacionadas ao dispositivo e às configurações Logitech antes de qualquer teste.
4. Registrar valores em repouso e ao mover cada eixo/pedal, incluindo intervalo bruto, intervalo normalizado, centro, ruído e sentido.

### Fase B — descobrir o mecanismo de configuração

Para cada opção (faixa de rotação, sensibilidade, mola central, força, pedais invertidos):

1. Capturar o estado inicial do Registro e os arquivos de perfil.
2. Alterar **uma única opção** no LGS, aplicar, fechar e reabrir o programa.
3. Comparar as alterações no Registro e nos arquivos.
4. Comparar a saída do eixo no painel de controle e no monitor do Hub.
5. Se necessário, usar ferramentas de diagnóstico autorizadas para observar chamadas de API e tráfego USB; documentar versão, método e limitações.
6. Repetir com LGS fechado e após reinicialização para separar configuração persistente de comportamento transitório.

**Regra:** não publicar conclusões de mecanismo baseadas apenas em correlação de XML. Registrar evidência observável e nível de confiança.

### Fase C — desenho recomendado para o Hub

- Criar uma camada de **descoberta de dispositivo** independente da UI.
- Criar adaptadores separados para **HID**, **configuração do driver/Registro** e **DirectInput/FFB**, cada um com capacidades explícitas.
- Expor uma interface interna comum para eixos, botões, configuração e FFB, sem assumir que todos os dispositivos implementam todos os recursos.
- Implementar inversão como transformação configurável no ponto mais apropriado e documentado. Evitar inverter simultaneamente no driver, no Hub e no jogo.
- Manter “ler estado atual” separado de “escrever/aplicar configuração”, com validação, logs e rollback.
- Adicionar testes de regressão para eixos normalizados, limites, centro, inversão, pedais combinados/separados e reconexão USB.
- Preservar as proteções de segurança do Windows; qualquer teste com driver/filtro de kernel deve ser isolado e reversível.

## Matriz de hipóteses e evidências

| Pergunta | Evidência necessária | Conclusão permitida |
|---|---|---|
| O perfil XML inverte um pedal? | XML + resultado reproduzível no jogo | O perfil está associado ao comportamento; mecanismo ainda não determinado |
| O LGS altera o Registro? | Diff de chaves antes/depois de aplicar a opção | A opção grava os valores identificados |
| O driver lê esses valores? | Evidência adicional de leitura/efeito após reinicialização ou rastreamento | Inferência mais forte; não basta observar a gravação |
| A inversão é aplicada no Hub? | Comparar entrada bruta com saída transformada do Hub | Transformação localizada no Hub |
| A inversão é aplicada pelo driver? | Comparação controlada e evidência de comportamento no caminho do driver | Só afirmar se o experimento isolar essa camada |
| FFB funciona por DirectInput? | Teste de efeito, estado do dispositivo e logs/API | Confirma o caminho testado, não todos os efeitos ou versões |

## Prioridades de implementação sugeridas

1. **Alta — diagnóstico:** página de informações do dispositivo, driver/INF, IDs e capacidades detectadas.
2. **Alta — telemetria de eixos:** mostrar valores brutos e normalizados, mínimo/máximo, centro e opção de inversão apenas para diagnóstico.
3. **Alta — rastreabilidade de configuração:** log de cada valor lido/escrito, origem (perfil/Registro/HID/API) e resultado.
4. **Média — testes comparativos LGS:** ferramenta guiada para capturar estado antes/depois e gerar relatório redigido, sem incluir dados pessoais do sistema.
5. **Média — adaptadores explícitos:** não misturar código de HID, Registro e FFB numa única rotina.
6. **Antes de qualquer driver próprio:** confirmar se as interfaces existentes cobrem a funcionalidade e se a correção pode ser feita em modo usuário.

## Limites e ressalvas

- A documentação pública consultada explica a arquitetura HID do Windows e oferece referência de integração DirectInput/FFB, mas não revela o protocolo interno completo entre LGS, driver legado e firmware do G27.
- Nomes de chaves de Registro, formatos de relatórios proprietários e chamadas internas precisam ser confirmados no sistema de teste; não devem ser inventados ou generalizados para todas as versões.
- O comportamento de um perfil pode variar conforme versão do LGS, pacote de driver, jogo e modo de eixos.
- Esta nota não recomenda modificar binários Logitech nem desativar mecanismos de segurança do Windows.

## Referências

1. Microsoft Learn, [HID architecture](https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-architecture).
2. Microsoft Learn, [HID client drivers](https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/hid-client-drivers).
3. Microsoft Learn, [Human Interface Devices — API e IOCTLs](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/_hid/).
4. Logitech G, [Developer Alliance — SDK para volantes](https://www.logitechg.com/pt-br/programs/developer-alliance).
5. Projeto comunitário, [Legacy Logitech wheels for Windows 11](https://github.com/Mysli0210/Legacy-Logitech-wheels-for-W11).
6. Projeto analisado, [Legacy Wheel Hub](https://github.com/leonardo201800478/legacy-wheel-hub).

---
*Última revisão documental: 2026-10-20. Atualizar esta nota quando novas capturas experimentais ou documentação oficial forem adicionadas.*
