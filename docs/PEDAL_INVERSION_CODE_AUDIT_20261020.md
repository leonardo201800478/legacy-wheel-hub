# Auditoria da inversão de pedais via DirectInput — 2026-10-20

## Escopo

Auditoria estática da implementação publicada em `LegacyWheelHub.py` e `dinput8-proxy/src/`, após a compilação local x64 da DLL. Esta auditoria não substitui um teste em execução com o Logitech G27 e o MAME.

## Resultado da compilação local reportado

- CMake configurou o projeto com o gerador Visual Studio 2026 e MSVC x64.
- `cmake --build build\\dinput8-x64 --config Release` gerou `build\\dinput8-x64\\Release\\dinput8.dll`.
- `dumpbin /exports` mostrou as seis exportações esperadas, incluindo `DirectInput8Create`.
- A compilação emitiu avisos de redefinição de `NOMINMAX` e `WIN32_LEAN_AND_MEAN`; não foram erros fatais.
- `git status --short` não mostrou alterações locais pendentes.

## Achados

### 1. A inversão ainda não está configurada para nenhum eixo por padrão

Em `LegacyWheelHub.py`, os campos `pedal_axis_throttle_offset`, `pedal_axis_brake_offset` e `pedal_axis_clutch_offset` têm default `-1`. O publicador do Registro mantém esse sentinel e `profile_needs_proxy()` só considera a inversão motivo para instalar a proxy se um pedal estiver habilitado **e** seu offset for não negativo.

Consequência: marcar a opção de inversão, sem uma configuração explícita do offset, não produz transformação no jogo. Isso é intencionalmente fail-closed, mas significa que a funcionalidade ainda não está pronta para uso final.

### 2. O offset é um deslocamento em bytes de um formato DirectInput, não um índice de eixo genérico

`LwhApplyPedalInversion()` altera quatro bytes no buffer de `GetDeviceState` a partir do offset configurado e interpreta esses bytes como `LONG`. Isso só é válido se o offset e o tipo de dado forem compatíveis com o `DIDATAFORMAT` usado pelo jogo.

Os índices de eixos HID/SDL, posições de relatório HID e offsets de `DIDATAFORMAT` são espaços diferentes e não podem ser intercambiados. A implementação atual encaminha `SetDataFormat` sem registrar ou validar o formato solicitado. Não existe ainda uma etapa de calibração/descoberta que associe com segurança acelerador, freio e embreagem aos offsets do jogo.

### 3. O intervalo numérico também precisa corresponder ao objeto DirectInput

O algoritmo calcula `minimum + maximum - current`, mas os defaults são 0 e 65535. Isso não é universal: objetos DirectInput podem ter intervalos configurados pelo jogo e os valores podem ser assinados. O código evita escrever fora do buffer e ignora valores fora do intervalo informado, mas limites incorretos podem fazer a inversão não acontecer ou transformar um eixo incorretamente.

Antes de ativar qualquer offset, o Hub precisa obter ou configurar os limites reais do objeto e validar o formato/tamanho do dado.

### 4. O caminho de execução precisa ser comprovado para o jogo-alvo

A transformação está em `IDirectInputDevice8::GetDeviceState` no wrapper. Ela não afeta automaticamente leituras feitas por Raw Input, WinMM, SDL/HID ou por interfaces COM que contornem esse wrapper. O MAME pode usar diferentes backends conforme sua configuração; ainda não há evidência de que o caminho de leitura de eixos da configuração do usuário passe por esse método.

### 5. A chave de Registro por jogo merece validação de identidade do executável

O lado C++ deriva a chave do caminho retornado por `GetModuleFileNameW(NULL, ...)`. O lado Python aplica `resolve_game_exe()` antes de construir a chave. Se o perfil apontar para um launcher que seja resolvido para outro executável, ou se os caminhos efetivos divergirem, a DLL poderá consultar uma chave diferente da que o Hub escreveu. A chave deve ser verificada com o executável real do processo-alvo.

### 6. Os avisos de macros são limpeza de build, não bloqueio funcional

O CMake já define `NOMINMAX` e `WIN32_LEAN_AND_MEAN` para o alvo, e esses macros também aparecem nos arquivos-fonte/headers. Isso explica os avisos C4005. É recomendável centralizar as definições no CMake ou proteger as definições com `#ifndef`, sem alterar a lógica de runtime.

## Conclusão

**Status: compilável, mas inversão em jogo ainda não validada nem configurável de ponta a ponta.** Não instalar a DLL para uso real apenas com base no sucesso da compilação/exportação.

## Próximos passos recomendados

1. Adicionar um mecanismo de diagnóstico explícito para registrar, apenas quando solicitado, o `DIDATAFORMAT` recebido por `SetDataFormat`: tamanho do estado, `dwDataSize`, `dwNumObjs` e os GUIDs/`dwOfs`/`dwType` dos objetos. Não registrar pacotes de eixo continuamente por padrão.
2. Definir uma associação verificável entre o pedal físico e o objeto DirectInput, por calibração/seleção explícita; não inferir a semântica do pedal apenas por GUID X/Y/Z.
3. Determinar os limites reais do objeto por `DIPROP_RANGE` quando disponível, ou fornecer uma configuração explícita validada.
4. Confirmar se o MAME está usando DirectInput e se as chamadas passam por `DirectInput8Create` e `GetDeviceState`. Se usa outro backend, esta proxy não resolve esse caminho.
5. Só então implementar e testar a inversão, incluindo eixo neutro, curso mínimo/máximo, eixos não selecionados, botões e FFB.
6. Remover os avisos C4005 em uma alteração separada e repetir build x64; depois avaliar build x86 se o jogo-alvo for de 32 bits.

## Critério de aceitação

Para cada pedal configurado, com inversão ativada, um teste deve demonstrar que o valor entregue ao jogo é `min + max - valor_original` nos limites reais do objeto; pedais não configurados, volante, botões e FFB devem permanecer inalterados. O teste deve identificar explicitamente o backend de entrada usado pelo executável.

## Atualização posterior da auditoria — diagnóstico implementado

Foi adicionado um diagnóstico opt-in em `dinput8-proxy/src/proxy.h`:

- Ativação somente quando o processo herda `LWH_DI_FORMAT_DEBUG=1`.
- Registra o HRESULT de `SetDataFormat`, os metadados do `DIDATAFORMAT` e os objetos (GUID, `dwOfs`, `dwType`, `dwFlags`).
- Limita a lista a 256 objetos por chamada e respeita `dwObjSize` como stride.
- Não registra valores de eixo em tempo real e não altera o buffer de eixos.
- A documentação de compilação e execução está em [DIAGNOSTICS_DIRECTINPUT_DATA_FORMAT.md](DIAGNOSTICS_DIRECTINPUT_DATA_FORMAT.md).

Commits relacionados:
- `c2d9b2a06711fc35fd73672b1dfbf6fe659cc5d0` — diagnóstico opt-in inicial.
- `f340f08455fb5cec787a26a59a48d8d08da1d920` — respeitar o stride dos objetos.
- `73579c6b5ae90bd2c293a57b7e6d0c8a02621bdf` — validar o cabeçalho antes de ler os campos.

A implementação ainda precisa ser recompilada e exercitada em um processo de teste. Não há confirmação de runtime até esse teste ocorrer.
