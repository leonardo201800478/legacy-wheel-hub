# Status de release e cadeia de proveniência — 2026-10-20

## Resultado da verificação

No momento desta auditoria, a API pública do GitHub retorna zero releases publicados para este repositório. O README anteriormente instruía o usuário a baixar `LegacyWheelHub_Setup.exe` e ignorar o aviso do SmartScreen, mas não havia release correspondente disponível para verificar.

Também não foi localizado no branch `main` um projeto de instalador ou uma configuração de empacotamento que conecte o executável principal às DLLs proxy compiladas pelo CI. A árvore contém o código Python, o projeto CMake da proxy e o workflow de compilação, mas não um arquivo de configuração PyInstaller, Inno Setup, WiX ou equivalente que estabeleça a cadeia do instalador referido pelo README.

Isso significa que não é possível demonstrar, a partir do repositório público atual, como foram produzidas as quatro DLLs que o Kaspersky removeu do computador. A ausência de evidência de empacotamento não prova que os binários sejam maliciosos nem que sejam falsos positivos.

## Compilação de proxy verificada

Workflow: [Build DirectInput proxy](https://github.com/leonardo201800478/legacy-wheel-hub/actions/workflows/build-dinput8-proxy.yml)

Execução: [run #5 — commit 0a1fd2926630a41f7dca4f5022e0f38813f92eae](https://github.com/leonardo201800478/legacy-wheel-hub/actions/runs/39440782670)

Resultado observado:
- job Win32: sucesso;
- job x64: sucesso;
- validação dos cabeçalhos MZ/PE e da arquitetura: sucesso;
- geração de `provenance.json` com commit de origem, arquitetura, máquina PE, tamanho e SHA-256: sucesso;
- upload de dois artefatos do CI: sucesso.

Os artefatos do workflow são saídas de desenvolvimento. O sucesso do CI não é uma certificação de segurança, não autentica os binários antigos e não substitui testes funcionais nem análise antimalware.

## Orientação de segurança

- Não desative antivírus, SmartScreen, Integridade da Memória ou outras proteções para executar o aplicativo.
- Não restaure as DLLs removidas nem crie exclusões apenas para contornar a detecção.
- Preserve o nome exato da detecção, horário e hashes disponíveis.
- Caso seja necessário investigar o arquivo, obtenha-o de uma fonte controlada e envie-o ao fornecedor do antivírus pelo canal oficial de análise de falso positivo/malware. Não o execute durante a investigação.
- Não substitua a `dinput8.dll` de outros plugins, como o FFB Arcade Plugin do MAME, sem uma estratégia de encadeamento explicitamente implementada e testada.

## Critérios para publicar um instalador verificável

Antes de voltar a distribuir um instalador:
1. Identificar e versionar a configuração real de empacotamento da aplicação.
2. Fazer o pipeline compilar a proxy a partir do commit identificado e incorporar somente esses artefatos ao pacote.
3. Gerar um manifesto final do pacote com versão, commit de origem, arquitetura, tamanho e SHA-256 de cada binário.
4. Automatizar uma verificação de integridade do pacote e testar instalação, desinstalação, atualização e comportamento sem proxy.
5. Publicar o pacote e o manifesto juntos em uma GitHub Release identificada por tag.
6. Considerar assinatura de código Authenticode e submeter amostras ao fornecedor de antivírus; a assinatura não garante que um arquivo seja seguro nem impede toda detecção.

Até que esses critérios sejam atendidos, não se deve apresentar um novo instalador como equivalente ao pacote que foi removido pelo Kaspersky.
