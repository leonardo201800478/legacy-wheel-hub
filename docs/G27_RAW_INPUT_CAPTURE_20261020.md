# Análise das capturas Raw Input do Logitech G27 — 2026-10-20

**Origem:** arquivos JSON/CSV enviados pelo usuário após a correção de assinaturas Win32 na ferramenta `tools/g27_windows_raw_input_diagnostics.py`.
**Escopo:** análise estática dos relatórios registrados; não foi executada no PC do usuário nem é uma captura elétrica do barramento USB.

## Resultado principal

A correção melhorou o resumo por dispositivo: nas duas capturas, todos os relatórios registrados foram associados a um único caminho HID que contém `VID_046D&PID_C29B`, identificador compatível com o Logitech G27. Não houve erros reportados pelo script.

| Arquivo JSON | Duração | Relatórios | Média aproximada | Tamanho de cada relatório |
|---|---:|---:|---:|---:|
| `g27_raw_hid_20261020_095516.json` | 60,003 s | 4.058 | 67,6/s | 13 bytes |
| `g27_raw_hid_20261020_095628.json` | 60,003 s | 4.108 | 68,5/s | 13 bytes |

O resumo `report_summary_by_device` contém apenas um dispositivo em cada captura e contabiliza todos os relatórios nesse caminho. O caminho HID observado foi:

```text
\\?\HID#VID_046D&PID_C29B#7&396d53e7&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}
```

A ferramenta registrou as coleções de uso Joystick (`0x01/0x04`) e Game Pad (`0x01/0x05`). O relatório específico do G27 foi observado pelo caminho HID, mas ainda não foi decodificado por descritor.

## Variação dos bytes

A comparação dos CSVs mostra que os payloads não são constantes: vários bytes mudam ao longo da captura. Em ambas, cada relatório tem 13 bytes; o byte de índice 0 permaneceu `00` e o byte de índice 8 permaneceu `80`.

- Na captura das 09:55:16, o byte de índice 12 permaneceu `FF` em todos os 4.058 relatórios.
- Na captura das 09:56:28, o byte de índice 12 variou, com 186 valores distintos observados.
- Outros bytes também variaram nas duas capturas, inclusive os índices 4, 5, 6, 7, 9 e 10.

Isso demonstra que os relatórios carregam campos variáveis, mas **não permite afirmar qual byte representa direção, acelerador, freio, embreagem ou botões**. Atribuir significados exige recuperar o descritor HID e interpretar os campos conforme suas páginas/IDs de uso, tamanhos e limites lógicos.

## O que a correção confirma — e o que não confirma

**Confirmado pelos arquivos:**
1. O script completou as duas capturas de aproximadamente 60 segundos sem registrar erros.
2. Os relatórios registrados foram agrupados pelo caminho HID que contém `VID_046D&PID_C29B`.
3. O JSON inclui `report_summary_by_device`, com contagem e tamanho dos relatórios.
4. O tamanho observado foi consistentemente de 13 bytes por relatório.

**Ainda não confirmado:**
1. Que todos os campos de metadados de `RIDI_DEVICEINFO` estejam corretos: o JSON atual apresenta inventário por tipo e caminho, não valores decodificados de VID/PID/Usage para cada dispositivo.
2. Qual campo corresponde a cada eixo, botão ou estado.
3. Se o LGS está com o perfil do jogo ativo ou se a inversão de eixos foi aplicada.
4. Como o LGS comunica essas opções ao driver.

As capturas não contêm marcações de tempo feitas durante cada movimento (volante, pedal específico ou botão). Por isso, não é seguro correlacionar um byte com uma ação específica apenas pela sequência gravada.

## Próxima etapa recomendada

1. Implementar uma ferramenta de inventário HID que obtenha o descritor do dispositivo por APIs documentadas do Windows, usando os dados de preparação HID (`HidD_GetPreparsedData`, `HidP_GetCaps` e capacidades de botão/valor).
2. Interpretar os campos do descritor e, então, comparar os valores decodificados com o CSV Raw Input.
3. Fazer uma nova captura curta e controlada: repouso, giro apenas do volante, acelerador isolado, freio isolado, embreagem isolada e botões. Anotar os horários aproximados de cada etapa.
4. Só depois comparar uma alteração de cada vez no perfil LGS. Não inferir aplicação da inversão a partir do XML isoladamente.

**Segurança:** esta ferramenta permanece somente de leitura. Não envia relatórios de saída, comandos de force feedback, alterações de Registro ou modificações de driver. Não é necessário desativar Integridade da Memória ou outras proteções do Windows para esta etapa.

## Arquivos da captura analisada

- `g27_raw_hid_20261020_095516.json` e `g27_raw_hid_20261020_095516.csv`
- `g27_raw_hid_20261020_095628.json` e `g27_raw_hid_20261020_095628.csv`

Os arquivos originais foram fornecidos na conversa de diagnóstico. Este documento registra os resultados resumidos; não afirma que os CSVs foram adicionados ao repositório.
