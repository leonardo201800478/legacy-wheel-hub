# Implementação da inversão de pedais — estado e integração

## Estado atual

A configuração por perfil já existe em `PROFILE_DEFAULTS` e é salva em `settings.json`:
- `invert_throttle`
- `invert_brake`
- `invert_clutch`

O callback `_on_pedal_invert` grava a opção no perfil selecionado. Os campos de offset e limites também foram acrescentados ao perfil, com offset `-1` como sentinela de “não mapeado”:
- `pedal_axis_throttle_offset`, `pedal_axis_brake_offset`, `pedal_axis_clutch_offset`
- `pedal_axis_<pedal>_min` e `pedal_axis_<pedal>_max`

Não é seguro preencher os offsets com os índices SDL: os offsets DirectInput são posições em bytes dentro do buffer de estado que o jogo solicita.

## Código adicionado

- `pedal_inversion.py`: transformação matemática isolada e testes unitários Python.
- `dinput8-proxy/src/pedal_inversion.h`: adaptador nativo que lê flags, offsets e limites do Registro por executável e inverte um valor `LONG` no buffer retornado por DirectInput.
- `dinput8-proxy/src/proxy.h`: `GetDeviceState` encaminha primeiro para o dispositivo real e aplica a transformação configurada ao buffer de saída. As outras chamadas COM e o pipeline de FFB/LUT permanecem encaminhados ao objeto real.
- `dinput8-proxy/CMakeLists.txt`: definição inicial de build MSVC para Windows.
- `LegacyWheelHub.py`: publica a configuração por jogo em `HKCU\Software\LegacyWheelHub\Games\<chave-do-executável>`.

A transformação matemática é `min + max - valor`. O adaptador verifica se o offset está alinhado, cabe inteiramente no buffer e se o valor está dentro dos limites configurados; caso contrário, não altera esse campo. A inversão permanece inativa quando o offset está em `-1`.

## Limitações que ainda impedem considerar a função concluída

1. **O mapeamento de offsets ainda não está disponível na interface gráfica.** Os offsets ficam desativados por padrão. Não altere-os por tentativa: é preciso identificar o formato de dados usado pelo jogo e o offset exato de cada pedal.
2. A interceptação só alcança jogos que chamam `DirectInput8Create` e leem os estados por `IDirectInputDevice8::GetDeviceState` através do proxy. Jogos que usam Raw Input, SDL ou outra API podem ignorar essa camada.
3. O proxy precisa ser reconstruído e empacotado para a arquitetura do jogo (x86 ou x64). A presença de `CMakeLists.txt` não significa que a DLL já tenha sido compilada nem distribuída.
4. O comportamento precisa ser validado no MAME e em outro jogo DirectInput, com um pedal por vez, flags ligadas/desligadas, perfil correto e FFB funcionando. Essa validação ainda não foi executada nesta alteração.
5. O adaptador de estado não altera o driver nem o relatório HID do volante; modifica somente a cópia de estado entregue por DirectInput ao jogo.

## Próxima etapa obrigatória

1. Criar um diagnóstico DirectInput para registrar, manualmente, o `DIDATAFORMAT` solicitado pelo jogo e os objetos/offsets usados.
2. Usar o diagnóstico para implementar uma seleção de eixo por pedal na UI, com validação do formato e limites reais.
3. Compilar o proxy nas arquiteturas suportadas e integrá-lo ao empacotamento de release sem substituir DLLs existentes por builds não validados.
4. Testar no MAME se a API interceptada é de fato o caminho de entrada consumido; se não for, escolher uma camada compatível com a API real sem desativar as proteções do Windows.
5. Confirmar que volante, botões, eixos não mapeados e Force Feedback continuam funcionando.

Não declarar a inversão como funcional apenas porque a opção foi salva no perfil ou porque o proxy foi carregado. A evidência necessária é o valor do eixo alterado no jogo-alvo.
