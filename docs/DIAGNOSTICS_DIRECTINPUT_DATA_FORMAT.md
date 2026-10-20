# Diagnóstico opt-in do formato de dados DirectInput

## Objetivo

Registrar os metadados do formato que o jogo entrega a `IDirectInputDevice8::SetDataFormat`, para descobrir offsets de objetos DirectInput antes de configurar a inversão de pedais.

O diagnóstico foi adicionado ao wrapper em `dinput8-proxy/src/proxy.h`. Ele não tenta identificar automaticamente qual objeto é acelerador, freio ou embreagem e não altera o buffer de eixos.

## Privacidade e impacto

O diagnóstico fica desligado por padrão. Ele só registra quando o processo do jogo herda a variável de ambiente:

```text
LWH_DI_FORMAT_DEBUG=1
```

Quando habilitado, registra o HRESULT, os campos `DIDATAFORMAT` (`dwSize`, `dwObjSize`, `dwFlags`, `dwDataSize`, `dwNumObjs`) e, para cada objeto (até o limite de 256 objetos por chamada), o GUID, `dwOfs`, `dwType` e `dwFlags`. Não registra valores de eixo em tempo real. A lista é limitada para manter o volume de log controlado.

A saída vai para `proxy.log` no diretório definido pelo Hub/Registro, com fallback para `%LOCALAPPDATA%\\LegacyWheelHub\\proxy.log`.

## Compilar

No PowerShell em que MSVC e CMake já estão inicializados:

```powershell
cmake -S dinput8-proxy -B build\dinput8-x64 -A x64
cmake --build build\dinput8-x64 --config Release
```

DLL de saída:

```text
build\dinput8-x64\Release\dinput8.dll
```

## Executar um teste de diagnóstico

1. Não sobrescreva uma DLL `dinput8.dll` já existente no diretório do jogo. Se existir, identifique primeiro a origem e faça backup antes de qualquer experimento.
2. Use somente uma cópia de teste da proxy recém-compilada ao lado do executável que realmente inicializa DirectInput. A proxy precisa ser carregada pelo processo-alvo para que o diagnóstico seja executado.
3. Inicie o processo-alvo a partir do PowerShell que definiu a variável de ambiente. Exemplo genérico:

```powershell
$env:LWH_DI_FORMAT_DEBUG = "1"
& "C:\caminho\para\o\executavel-alvo.exe"
```

Adicione os argumentos normais do emulador/jogo, se necessários. A variável é herdada pelo processo e fica ativa apenas nesse terminal e nos processos iniciados a partir dele.

4. Abra o emulador/jogo, entre na configuração de controles e faça o programa inicializar o dispositivo. Encerre-o normalmente.
5. Consulte `proxy.log` e procure linhas `DI SetDataFormat`, `DI format:` e `DI object[`.
6. Desative o diagnóstico ao terminar, fechando o terminal ou executando:

```powershell
Remove-Item Env:LWH_DI_FORMAT_DEBUG -ErrorAction SilentlyContinue
```

## Interpretação

- `dwOfs` é um deslocamento em bytes dentro do estado DirectInput descrito por aquele formato; não é o índice de eixo SDL nem o índice do relatório HID.
- `dwType` informa o tipo/semântica DirectInput do objeto, mas não basta sozinho para concluir qual pedal físico ele representa.
- `dwDataSize` é o tamanho do buffer de estado esperado para aquele formato.
- GUIDs de objetos e seus offsets devem ser correlacionados com o dispositivo real e, se necessário, com uma enumeração de objetos/props ou um teste controlado dos pedais.
- Se não aparecer nenhuma linha, isso não prova que o jogo não usa DirectInput: pode significar que a proxy não foi carregada, que o processo usa outra API/backend ou que o formato ainda não foi configurado durante a execução observada.

## Limitação importante

O diagnóstico é uma etapa de descoberta, não uma prova de que o MAME lê os eixos por `GetDeviceState`. A transformação de inversão continua inerte enquanto os offsets não forem configurados explicitamente. Não defina offsets a partir de suposições e não habilite a inversão até confirmar o formato, o tipo de dado, os limites e o caminho de entrada efetivamente usado pelo jogo.
