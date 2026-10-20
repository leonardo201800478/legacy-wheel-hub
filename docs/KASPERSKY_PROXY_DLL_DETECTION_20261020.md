# Detecções do Kaspersky nas DLLs proxy — 2026-10-20

## Status

**Incidente aberto.** O Kaspersky reportou a exclusão das quatro DLLs `dinput8.dll` da instalação original do Legacy Wheel Hub. A detecção está confirmada pelo relatório fornecido pelo usuário; a natureza dos binários e a causa da detecção ainda não foram determinadas.

## Evidência reportada

Data/hora dos eventos: 20/10/2026 11:29. Ação: `Excluído(s)`.

| Caminho relativo à instalação | Detecção |
|---|---|
| `_internal/assets/proxy/x86/dinput8.dll` | `Trojan.Win32.Agent.xcgcwf` |
| `_internal/assets/proxy/x64/dinput8.dll` | `Trojan.Win32.Agent.xcgcwd` |
| `assets/proxy/x86/dinput8.dll` | `Trojan.Win32.Agent.xcgcwf` |
| `assets/proxy/x64/dinput8.dll` | `Trojan.Win32.Agent.xcgcwd` |

Raiz reportada: `C:\Program Files\Legacy Wheel Hub`.

O usuário informou que não houve detecção/exclusão do executável principal; as quatro entradas reportadas são das DLLs proxy.

## O que sabemos e o que não sabemos

- O relatório demonstra que o Kaspersky classificou e excluiu esses arquivos; não demonstra, sozinho, se a classificação é correta.
- O nome de detecção, isoladamente, não permite concluir que é malware real ou falso positivo.
- Uma proxy de DirectInput intercepta/encaminha chamadas de API, comportamento que pode merecer revisão, mas isso não prova que esse seja o motivo da detecção.
- Durante a tentativa de inspeção, a leitura/hash e o `dumpbin /exports` falharam após os arquivos serem excluídos ou ficarem inacessíveis.
- Não há SHA-256 dos binários originais, nem correspondência confirmada entre esses arquivos e o código-fonte publicado ou a compilação local x64 de 54.272 bytes.
- Código-fonte disponível e build bem-sucedido não constituem, por si só, prova de segurança do binário distribuído.

## Próximos passos seguros

1. Não restaurar os arquivos nem adicionar uma exclusão global no Kaspersky antes de análise adicional.
2. Guardar os detalhes completos dos eventos e consultar os relatórios do Kaspersky.
3. Revisar o código-fonte das proxies e o processo de build/empacotamento para x86 e x64.
4. Quando viável, compilar em ambiente controlado a partir do código-fonte revisado e registrar hashes SHA-256 e exportações.
5. Se houver evidências de falso positivo, submeter o binário reconstruído e os detalhes técnicos ao fornecedor do antivírus para análise, em vez de desativar a proteção.

## Critério de encerramento

O incidente só deve ser encerrado após análise do código e do processo de distribuição, com hashes e arquitetura dos binários analisados registrados. Até lá, a causa da detecção permanece **indeterminada**.
