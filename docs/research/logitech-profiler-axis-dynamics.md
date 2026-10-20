# Investigação: como o Logitech Profiler aplica `AxisDynamics` ao G27

**Estado:** investigação aberta; ainda não foi identificado o protocolo interno do Logitech Gaming Software (LGS).  
**Hardware alvo:** Logitech G27.  
**Software de referência:** Logitech Gaming Software / Logitech Profiler 5.10, SDK Steering Wheel SDK for PC 1.00.002 e Legacy Wheel Hub.  
**Perfil de reprodução:** perfil `MAME.xml` fornecido pelo usuário, associado a `mame.exe`.

## Objetivo

Descobrir como o Logitech Profiler transforma os eixos configurados em `AxisDynamics` e como essa configuração chega à camada que o MAME lê. A finalidade é avaliar uma implementação compatível no Legacy Wheel Hub, preservando o driver oficial da Logitech e sem desativar Integridade da Memória/Isolamento do Núcleo.

Não assumir de antemão que a transformação é executada pelo driver. O LGS pode processar os eixos em user mode, configurar um componente do driver, ou combinar as duas abordagens.

## Evidências disponíveis

### 1. Perfil MAME.xml

O perfil observado contém:

```xml
<Assignments DeviceModel="57">
  <AxisDynamics>
    <AxisDef Axis="R" Sign="-1" Acceleration="50" Speed="100"
             Deadzone="0" DeadzoneSign="0" />
    <AxisDef Axis="Z" Sign="-1" Acceleration="50" Speed="100"
             Deadzone="0" DeadzoneSign="0" />
  </AxisDynamics>
  <Mapping>
    <Source Type="Axis" ID="0" />
    <Destination Type="Axis" ID="1" />
  </Mapping>
  <Mapping>
    <Source Type="Axis" ID="2" />
    <Destination Type="Axis" ID="4" />
  </Mapping>
  <Mapping>
    <Source Type="Axis" ID="3" />
    <Destination Type="Axis" ID="8" />
  </Mapping>
</Assignments>
```

Observações:
- `Sign="-1"` é consistente com uma inversão de sinal, mas o XML sozinho não estabelece a fórmula nem o ponto da cadeia em que ela é aplicada.
- `Acceleration`, `Speed`, `Deadzone` e `DeadzoneSign` indicam parâmetros adicionais da transformação de eixo.
- `Mapping` define relações entre IDs de eixo de origem e destino; não presumir o significado sem correlacionar com leituras reais.
- `CombinePedals="false"` mantém os pedais separados. Isso não equivale à inversão.
- `GameOptions Enable="true"` e `AllowGameSettings="true"` habilitam as opções de jogo; não demonstram como `AxisDynamics` é executado.

### 2. SDK oficial

A análise do Steering Wheel SDK for PC 1.00.002 identificou propriedades públicas como `combinePedals`, `wheelRange`, ganhos de force feedback e opções de jogo. Não foi identificada uma propriedade pública dedicada à inversão individual dos pedais.

O SDK usa DirectInput e inclui comunicação específica de dispositivo, incluindo o caminho `IDirectInputDevice8::Escape` para propriedades suportadas. Isso comprova que existe um caminho de comunicação específico com o dispositivo/driver, mas não prova que o LGS envie `AxisDynamics` por esse caminho.

### 3. Separação de camadas

- **Perfil XML:** declara configurações por executável.
- **Processo LGS/Profiler:** pode carregar e interpretar o perfil.
- **Interface de configuração:** possível comunicação com driver ou serviço.
- **Caminho de entrada:** valores de eixo observados pelo jogo.
- **Legacy Wheel Hub:** sua transformação de telemetria não altera automaticamente os valores que aplicações externas recebem.

## Hipóteses a testar

| ID | Hipótese | Evidência que a confirmaria |
|---|---|---|
| H1 | O LGS transforma eixos em user mode antes de os expor ao jogo | O comportamento depende do processo/serviço do Profiler e desaparece quando ele deixa de processar o perfil; rastros apontam para uma camada de entrada em user mode |
| H2 | O LGS envia configuração persistente ao driver | Uma operação de configuração ocorre ao ativar o perfil, e a transformação permanece no caminho de entrada mesmo sem processamento contínuo do Profiler |
| H3 | O LGS envia comandos privados ao driver em tempo real | Captura correlacionada com ativação do perfil mostra comunicação de dispositivo recorrente ou comandos de configuração |
| H4 | O mapeamento ocorre numa camada intermediária do próprio LGS | O MAME recebe eixos transformados enquanto uma aplicação DirectInput de comparação, fora do contexto do perfil, recebe valores diferentes |

As hipóteses não são necessariamente mutuamente exclusivas.

## Plano experimental

### Etapa A — Estabelecer uma linha de base

1. Confirmar versão do LGS, versão do driver, VID/PID e instância do G27 no Gerenciador de Dispositivos.
2. Exportar uma cópia do perfil normal e do `MAME.xml`; não editar o perfil original durante os testes.
3. Com o Profiler aberto, medir os eixos com o perfil normal.
4. Ativar o perfil MAME e repetir exatamente os mesmos movimentos.
5. Registrar o eixo bruto, valor mínimo/máximo, centro, sentido de variação e resultado observado pelo MAME.
6. Repetir com o Profiler fechado e, separadamente, com o processo/serviço do Profiler encerrado apenas quando for seguro fazê-lo. Não desinstalar nem desabilitar o driver.

Usar um leitor DirectInput/HID de diagnóstico independente para medir eixos, se disponível. Não concluir que a inversão é global com base apenas no MAME, pois o comportamento pode depender da aplicação ou da camada que carrega o perfil.

### Etapa B — Process Monitor

Ferramenta: [Process Monitor — Microsoft Sysinternals](https://learn.microsoft.com/sysinternals/downloads/procmon).

1. Executar o Process Monitor com permissões adequadas e limpar a captura.
2. Filtrar por processos do Logitech Gaming Software/Profiler e por operações de acesso a arquivos, registro e dispositivos.
3. Capturar uma janela curta antes e depois de ativar o perfil MAME.
4. Procurar leituras do XML e mudanças em arquivos ou chaves de configuração.
5. Anotar os caminhos, processos, timestamps e resultados. Exportar o PML e um CSV filtrado para comparação.

Limitação: Process Monitor ajuda a descobrir carregamento de perfil, arquivos, registro e criação/acesso a handles, mas não decodifica por si só o payload de chamadas IOCTL nem prova o que o driver faz com um comando.

### Etapa C — Identificar interfaces de comunicação

Investigar chamadas e APIs relevantes, sem presumir que alguma delas é a usada pelo LGS:

- `CreateFile` / abertura de handles para dispositivos;
- `DeviceIoControl` / IOCTLs;
- `HidD_SetFeature` e `HidD_SetOutputReport`;
- DirectInput `IDirectInputDevice8::Escape`;
- comunicação IPC entre processos/serviços, se observada.

Primeiro identificar quais executáveis e DLLs estão envolvidos. Depois escolher um método de rastreamento compatível com a arquitetura (x86/x64) e a versão do Windows. Registrar a sequência temporal e os parâmetros que puderem ser observados sem alterar o comportamento do driver.

Cuidados:
- Não enviar IOCTLs ou comandos HID especulativos ao volante.
- Não editar memória de processo nem instalar filtros de driver nesta fase.
- Não desativar Integridade da Memória, Isolamento do Núcleo ou outras proteções do Windows.
- Tratar buffers binários capturados como desconhecidos até serem correlacionados com testes repetíveis.

### Etapa D — Correlacionar configuração e eixos

Executar uma matriz mínima de testes:

| Teste | Perfil ativo | Profiler em execução | Aplicação de medição | Resultado a registrar |
|---|---|---|---|---|
| T1 | Normal | Sim | Leitor DirectInput | Eixos e faixa de valores |
| T2 | MAME | Sim | Leitor DirectInput | Eixos e faixa de valores |
| T3 | Normal | Sim | MAME | Comportamento percebido no jogo |
| T4 | MAME | Sim | MAME | Comportamento percebido no jogo |
| T5 | MAME | Não, se o perfil permanecer aplicável | Leitor DirectInput | Se a transformação persiste |
| T6 | MAME | Sim, perfil alternado durante a captura | Leitor DirectInput | Momento de mudança e operações correlacionadas |

Se o perfil não puder ser aplicado sem o Profiler, marcar T5 como não aplicável; não forçar uma conclusão.

## Instrumentação e artefatos a guardar

- Versão do LGS/Profiler, SDK, Windows e driver.
- Cópias dos perfis XML utilizados.
- Logs do leitor de eixos com timestamps.
- Captura PML e exportação CSV do Process Monitor.
- Lista dos processos/DLLs observados e arquitetura (32/64 bits).
- Resultado de cada teste, com indicação clara do que foi medido e do que é inferência.

Não guardar tokens, credenciais ou outros dados pessoais nos artefatos.

## Critérios para conclusão

A comunicação com o driver só deve ser considerada identificada quando houver:
1. uma operação concreta correlacionada com a ativação/alteração do perfil;
2. evidência da interface utilizada (por exemplo, IOCTL ou chamada DirectInput específica);
3. repetição do mesmo comportamento em testes controlados;
4. confirmação independente de que o valor de eixo visto pela aplicação mudou.

Se apenas a abertura de um dispositivo for observada, isso não demonstra que a inversão é configurada por esse dispositivo. Se os eixos mudarem apenas no MAME, investigar também o contexto do perfil e o caminho de entrada utilizado pelo jogo.

## Próxima decisão de implementação

- **Transformação em user mode confirmada:** avaliar uma camada de entrada compatível com o Hub, isolada por perfil e processo, sem alterar o driver original.
- **Configuração de driver confirmada:** documentar o protocolo antes de considerar uma implementação; só usar comandos reproduzíveis e validados.
- **Resultado inconclusivo:** recolher rastros adicionais antes de escrever código de produção.

Não implementar a transformação em `TelemetryPanel.refresh()` como solução para jogos externos: ela só alteraria a visualização interna, não necessariamente os eixos que o jogo recebe.
