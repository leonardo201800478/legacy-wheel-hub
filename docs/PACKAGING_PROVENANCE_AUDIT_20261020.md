# Auditoria da cadeia de empacotamento da proxy — 2026-10-20

## Escopo e método

Foi inspecionada a árvore pública da branch `main`, o código de `LegacyWheelHub.py`, `dinput8-proxy/CMakeLists.txt`, `dinput8-proxy/src/dllmain.cpp`, o workflow `.github/workflows/build-dinput8-proxy.yml`, os artefatos de build versionados e o endpoint público de Releases do GitHub.

Esta auditoria é documental/estática. Não houve acesso aos arquivos binários que o Kaspersky excluiu da instalação local, ao ambiente que gerou o instalador, nem ao histórico privado de distribuição. Não foi executada a aplicação.

## Conclusões principais

**A cadeia de proveniência não está fechada.** O repositório contém o código-fonte e um workflow de compilação, mas não contém, na árvore atual, os arquivos de proxy em `assets/proxy/x86/dinput8.dll` e `assets/proxy/x64/dinput8.dll` usados pela aplicação. Também não foi localizado um arquivo de configuração de PyInstaller, script de instalador, definição de Inno Setup/WiX ou workflow que conecte os artefatos do workflow ao instalador distribuído.

O endpoint público de Releases consultado retornou uma lista vazia no momento da revisão. Portanto, o README orienta baixar `LegacyWheelHub_Setup.exe` de Releases, mas não foi possível recuperar por essa via um instalador nem os binários que ele contém.

## Descoberta adicional: release do repositório upstream

O metadata do fork identifica `Sadooo27/legacy-wheel-hub` como repositório pai. A release pública upstream `v1.1.5` foi publicada em 2026-09-07 e contém o asset `LegacyWheelHub_Setup.exe`, com 37.676.297 bytes. O GitHub fornece para esse asset o digest `sha256:6209121ce84d2761f0e73ca2b18403efcb75fffe1919cdaef56d02f80a9d69bc`.

- Release: https://github.com/Sadooo27/legacy-wheel-hub/releases/tag/v1.1.5
- Commit associado à tag: `971e17c0237c7c5699ba5003747062b3b24185ad`
- SHA-256 publicado no metadata do asset: `6209121ce84d2761f0e73ca2b18403efcb75fffe1919cdaef56d02f80a9d69bc`

A comparação textual de `dinput8-proxy/src/dllmain.cpp` entre a tag upstream `v1.1.5` e a branch `main` do fork retornou o mesmo blob SHA `75aa76327924abf0ea02e9d374e2c92d8072309f`. Isso mostra que esse arquivo-fonte específico é idêntico nos dois pontos, mas não prova que o instalador da release contenha as DLLs detectadas, nem que tenha sido o instalador usado pelo usuário. A aplicação Python do fork divergiu da versão upstream, e o conteúdo do binário do instalador não foi extraído nem executado nesta auditoria.

**Interpretação:** agora existe uma release upstream verificável como candidata de comparação, mas a cadeia para o pacote instalado continua sem confirmação. Não se deve presumir que o digest do instalador upstream corresponda ao arquivo baixado ou executado no computador do usuário sem calcular o hash desse arquivo específico e compará-lo com a fonte de download.

## Evidências do repositório

### 1. A aplicação carrega os assets de um diretório empacotado

Em `LegacyWheelHub.py`:
- `_resource_dir()` usa `sys._MEIPASS` quando disponível, comportamento típico de bundle one-file do PyInstaller.
- `_proxy_assets_dir()` procura `assets/proxy` dentro do diretório de recursos, do diretório do executável e do diretório do script.
- `install_proxy_for()` seleciona `assets/proxy/x86/dinput8.dll` ou `assets/proxy/x64/dinput8.dll` com base na arquitetura do executável do jogo e copia a DLL para a pasta do jogo.
- O código escreve um marcador `.lwh_proxy` ao lado da DLL instalada.

Isso explica como a aplicação **consome** as DLLs, mas não revela como elas foram construídas ou incorporadas ao pacote.

### 2. O workflow de compilação não empacota o aplicativo

`.github/workflows/build-dinput8-proxy.yml` compila Win32 e x64 com CMake/MSVC e envia cada `dinput8.dll` como artefato de CI. O workflow não:
- copia os binários para `assets/proxy/x86` e `assets/proxy/x64`;
- compila ou empacota `LegacyWheelHub.py`;
- cria `LegacyWheelHub_Setup.exe`;
- publica hashes SHA-256, metadados PE e manifesto de conteúdo do pacote;
- assina os binários ou o instalador.

Logo, esse workflow, isoladamente, não prova que as DLLs da instalação foram geradas a partir do código publicado.

### 3. Há artefatos de compilação versionados

A árvore `main` inclui a pasta `build/dinput8-x64` com arquivos gerados pelo CMake/MSBuild, incluindo `build/dinput8-x64/Release/dinput8.dll` com 52.224 bytes. Esses artefatos mostram que uma compilação x64 foi registrada no Git, mas não constituem prova de que a DLL é a mesma que estava no instalador: não há manifesto ligando seu hash criptográfico ao pacote distribuído. A presença de arquivos de build no repositório também dificulta separar claramente fontes auditáveis de saídas geradas.

A compilação local relatada anteriormente tinha 54.272 bytes; a diferença entre os dois tamanhos não prova adulteração. Configuração, versão do compilador, opções de linkagem e código-fonte usado podem alterar o resultado. A comparação correta exige SHA-256 e origem/commit conhecidos para cada binário.

### 4. A instalação original continha cópias duplicadas dos assets

O registro fornecido pelo usuário mostra detecções nas cópias:
- `_internal/assets/proxy/x86/dinput8.dll`
- `_internal/assets/proxy/x64/dinput8.dll`
- `assets/proxy/x86/dinput8.dll`
- `assets/proxy/x64/dinput8.dll`

O Kaspersky informou que excluiu os quatro arquivos. A duplicação entre `assets` e `_internal/assets` pode resultar da estrutura do pacote ou de como os recursos foram incluídos; sem o spec/configuração do empacotador e sem examinar o instalador, não é possível afirmar por que existem as duas cópias. A aplicação procura a primeira pasta de assets que encontrar, portanto o comportamento exato depende da estrutura final do bundle.

## Avaliação de risco

- **Confirmado:** o Kaspersky detectou e excluiu as quatro DLLs indicadas.
- **Confirmado:** o código da aplicação copia a DLL escolhida para a pasta do executável do jogo.
- **Confirmado:** o workflow público de CI compila DLLs, mas não mostra a ligação entre esses artefatos e o instalador.
- **Não confirmado:** se as DLLs detectadas são malware ou falso positivo.
- **Não confirmado:** se as DLLs do instalador foram construídas a partir do código atualmente publicado.
- **Não confirmado:** se as cópias duplicadas são intencionais ou um efeito colateral do empacotamento.

## Próximas ações recomendadas

1. Recuperar o projeto/ambiente usado para criar o instalador original: comando PyInstaller ou arquivo `.spec`, scripts de build, dependências e origem exata das DLLs.
2. Não restaurar as DLLs excluídas apenas para obter hashes. Em vez disso, compilar novas DLLs em um ambiente controlado a partir de um commit identificado.
3. Criar um workflow único de release que compile x86/x64, calcule SHA-256, valide arquitetura e exports, e gere um manifesto com commit, toolchain e hashes.
4. Fazer o empacotamento consumir diretamente esses artefatos verificados, sem cópias manuais não rastreadas; incluir no pacote somente um conjunto canônico de `assets/proxy`, salvo se houver justificativa técnica documentada para duplicação.
5. Publicar instalador, manifestos e artefatos com versões/commits rastreáveis. Considerar assinatura Authenticode para DLLs e instalador.
6. Enviar ao Kaspersky os novos binários reconstruídos, hashes e o relatório de finalidade do código para análise. A decisão de falso positivo deve vir do fornecedor, não de uma exclusão local.
7. Depois de restabelecida a proveniência, fazer testes funcionais e de compatibilidade em ambiente controlado, sem desativar proteções do Windows.

## Estado

**Cadeia de empacotamento: não rastreável com as evidências públicas atuais.** A auditoria localiza o ponto em que a aplicação consome os assets e o workflow que compila a proxy, mas falta o elo entre a compilação e os binários entregues aos usuários.


## Atualização de CI após a auditoria

Em 2026-10-20, o workflow `.github/workflows/build-dinput8-proxy.yml` foi atualizado para que cada artefato x86/x64 inclua `provenance.json` com:
- commit de origem;
- arquitetura solicitada;
- arquitetura PE validada no cabeçalho;
- tamanho do arquivo;
- hash SHA-256.

A etapa falha se a DLL não existir, se o cabeçalho MZ/PE estiver inválido ou se a arquitetura PE não corresponder à matriz do build.

Commit da alteração do workflow: `0a1fd2926630a41f7dca4f5022e0f38813f92eae`.

**Execução pós-alteração confirmada:** [GitHub Actions run #5](https://github.com/leonardo201800478/legacy-wheel-hub/actions/runs/39440782670) terminou com sucesso nos jobs Win32 e x64, incluindo geração dos manifestos e upload dos dois artefatos.

Hashes SHA-256 extraídos dos logs do build:
- **Win32:** 47.616 bytes; PE machine `0x014C`; SHA-256 `12a768a4ad27099f6c0db1e2332a1c3e7bd9b9030f47d56e0c38dc19c9f873bf`.
- **x64:** 54.272 bytes; PE machine `0x8664`; SHA-256 `599b21eb10f2fd140f9352f454d42ac2ffb38a6a6396b952afa10188dc4067d5`.

O tamanho da DLL x64 do CI coincide com o tamanho da compilação local relatada pelo usuário, mas o hash é diferente do hash local `271263248CB6DEFB41D5E5FC50E75B954FFAA0F37A8E0E8693E29E0F87DC28C7`. Portanto, são arquivos diferentes byte a byte; isso, isoladamente, não demonstra adulteração, pois compiladores, opções e fontes exatas podem variar.

A melhoria torna os artefatos recém-produzidos pelo CI rastreáveis. **A cadeia do instalador original continua aberta** até que o empacotamento real seja localizado, versionado e conectado aos artefatos verificados.
