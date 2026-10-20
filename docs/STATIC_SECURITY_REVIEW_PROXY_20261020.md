# Revisão estática de segurança — proxy DirectInput

Data: 2026-10-20  
Escopo: revisão do código-fonte publicado em `dinput8-proxy/src/dllmain.cpp`, `proxy.h`, `pedal_inversion.h`, `dinput8-proxy/src/dinput8.def`, `dinput8-proxy/CMakeLists.txt` e do workflow `.github/workflows/build-dinput8-proxy.yml`.

## Resumo executivo

**Resultado: revisão estática parcial; não é possível declarar os binários detectados como seguros ou como malware.**

Nos arquivos revisados, a finalidade aparente é uma proxy de DirectInput para encaminhar a API do Windows e interceptar parâmetros de force feedback (LUT) e estado de eixos configurados. Não identifiquei, nos trechos revisados, código explícito de comunicação de rede, roubo de credenciais, persistência ou injeção de código. Essa observação é limitada ao código-fonte examinado e não autentica os binários excluídos pelo Kaspersky, nem garante que o pacote instalado tenha sido gerado exatamente a partir desse código.

## Comportamentos legítimos esperados e potencialmente sensíveis para heurística

1. A DLL usa o nome conhecido `dinput8.dll` para ser carregada no lugar da biblioteca esperada pelo jogo.
2. Obtém o caminho da DLL DirectInput do Windows, copia-a para um nome temporário único e carrega a cópia para evitar colisão de nomes e recursão.
3. Encaminha as funções exportadas e envolve objetos COM de DirectInput para modificar parâmetros de FFB e, quando explicitamente configurado, valores de eixos.
4. Lê configurações por jogo em `HKCU\\Software\\LegacyWheelHub\\Games\\<chave>`.
5. Grava logs e um beacon de estado em locais configurados pelo Hub.
6. Pode abrir uma caixa de mensagem de diagnóstico se a variável de ambiente `LWH_PROXY_MSGBOX=1` for definida.
7. Apaga a cópia temporária da DLL real durante o desligamento.

São comportamentos coerentes com uma proxy, mas a combinação de interceptação de API, carregamento de DLL e cópia/carregamento de uma biblioteca temporária pode ser relevante para sistemas heurísticos. Não há evidência suficiente para afirmar que esse seja o motivo exato dos nomes de detecção Kaspersky.

## Achados técnicos

### 1. A proxy publicada tem seis exports

O arquivo `dinput8.def` exporta:
- `DirectInput8Create`
- `DllCanUnloadNow`
- `DllGetClassObject`
- `DllRegisterServer`
- `DllUnregisterServer`
- `GetdfDIJoystick`

O workflow atual compila Win32 e x64 e publica os binários como artefatos de CI, mas não inclui no próprio workflow um manifesto SHA-256, análise estática de binário, assinatura ou teste de execução.

### 2. Encaminhamento da DLL real

`dllmain.cpp` tenta copiar a DLL de System32 para um arquivo temporário com nome baseado no PID e carregá-la. Há fallback para carregar pelo caminho direto. O código tenta impedir que o handle resolvido seja a própria DLL proxy.

Esse fluxo é tecnicamente explicável pela prevenção de recursão, mas precisa ser documentado para análise de antivírus. Também merece revisão futura o trabalho realizado em `DllMain(DLL_PROCESS_DETACH)` — chamada de `FreeLibrary`, remoção do beacon e exclusão de arquivo sob o loader lock podem ser frágeis no desligamento do processo. Isso é uma preocupação de robustez, não prova de comportamento malicioso.

### 3. Inversão de pedais desativada sem configuração explícita

`pedal_inversion.h` não transforma eixos sem a flag de inversão habilitada e um offset válido. Valida alinhamento, tamanho do buffer e faixa numérica antes de gravar. O offset continua dependendo de identificação correta do formato DirectInput do jogo.

### 4. Logs e telemetria local

O diagnóstico de formato DirectInput é opt-in por `LWH_DI_FORMAT_DEBUG=1` e registra metadados do formato, não valores contínuos dos eixos. O código também registra eventos de FFB. A revisão não identificou envio de logs para um servidor remoto nos arquivos examinados.

### 5. Divergência entre binários

O usuário informou que as quatro DLLs da instalação original tinham 278.528 bytes (x64) e 231.424 bytes (x86), antes de serem excluídas pelo Kaspersky. A compilação local x64 reportada anteriormente tinha 54.272 bytes. Tamanho diferente não prova adulteração: compiladores, opções de build, conteúdo e dependências podem variar. Entretanto, sem os hashes dos binários originais e sem artefatos de CI equivalentes, não é possível confirmar que as DLLs instaladas correspondem ao código atual.

### 6. O workflow não vincula os artefatos ao instalador

O workflow `build-dinput8-proxy.yml` faz checkout, compila as duas arquiteturas e envia cada DLL como artefato. O workflow visto não copia as DLLs para `assets/proxy`, não constrói o instalador e não demonstra que os binários distribuídos pelo instalador vêm desse mesmo build. Essa lacuna de proveniência precisa ser resolvida antes de atribuir o comportamento do binário instalado ao código publicado.

## Recomendações priorizadas

1. **Proveniência:** automatizar a compilação x86/x64 e publicar SHA-256, arquitetura PE, lista de exports, versão do compilador e commit de origem junto aos artefatos.
2. **Empacotamento:** localizar e documentar o processo que gera o instalador e verificar que ele consome exatamente os artefatos de CI identificados por hash.
3. **Falso positivo:** submeter os hashes/arquivos reconstruídos e os nomes exatos das detecções ao Kaspersky para análise. Não criar exclusão global nem desativar a proteção como solução de contorno.
4. **Robustez:** revisar operações feitas em `DllMain(DLL_PROCESS_DETACH)` e transferir limpeza complexa para um caminho de desligamento seguro, se possível.
5. **Validação funcional:** executar testes controlados para confirmar carregamento, encaminhamento de DirectInput, FFB, inversão e logs, separadamente da análise antivírus.
6. **Distribuição:** considerar assinatura de código do binário e do instalador com certificado verificável, preservando a proveniência do build.

## Conclusão

O código examinado apresenta uma finalidade consistente com uma proxy de DirectInput e não revelou, nos arquivos revisados, uma função maliciosa explícita. Porém, a origem exata dos binários que o Kaspersky detectou não está comprovada. A discrepância de tamanho e a ausência de uma ligação documentada entre o workflow de build e os arquivos empacotados impedem uma conclusão de falso positivo.

**Estado:** revisão estática parcial concluída; análise dos binários distribuídos e da cadeia de empacotamento pendente.
