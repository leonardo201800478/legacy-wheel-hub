# Implementação da inversão de pedais — estado e contrato

A configuração por perfil já existe em `PROFILE_DEFAULTS` e é salva por `save_settings()` em `settings.json`:
- `invert_throttle`
- `invert_brake`
- `invert_clutch`

O callback `_on_pedal_invert` grava a opção no perfil selecionado. Portanto, não é necessário criar outro formato de persistência para esses três campos.

## Primeiro incremento de código

O módulo `pedal_inversion.py` define a transformação matemática independente da UI e do dispositivo. Para um eixo com mínimo `min`, máximo `max` e valor atual `x`, a inversão é:

```
x_invertido = min + max - x
```

Isso funciona tanto para eixos bipolares normalizados (-1..+1) quanto unipolares (0..1) ou valores inteiros, desde que sejam usados os limites reais reportados pela API de entrada. O módulo também resolve as flags individuais de cada perfil e contém testes unitários.

## Limite atual — integração necessária para chegar ao jogo

**Este incremento, isoladamente, ainda não inverte o eixo recebido pelo MAME.** Ele estabelece e testa a transformação que o adaptador de entrada deverá chamar. A camada HID/telemetria atual do Hub não é o caminho de entrada que o MAME consome.

O repositório contém a lógica Python de instalação do proxy `dinput8.dll` e artefatos DLL empacotados, mas não foi localizada, nesta revisão, a fonte nativa do proxy para alterar e reconstruir seu comportamento de entrada. O proxy descrito no código atual é usado para pós-processamento de FFB/LUT; não se deve ativá-lo como se já implementasse inversão de pedais.

## Próximo passo obrigatório

1. Recuperar/adicionar a fonte nativa e o processo de build do proxy DirectInput compatível com x86/x64.
2. Ler as flags do perfil correspondente ao executável-alvo, sem depender do LGS.
3. Interceptar o estado dos eixos de pedal na API de entrada que o jogo realmente usa e aplicar `apply_pedal_inversion` (ou a transformação equivalente nativa).
4. Encaminhar sem alteração todos os outros eixos, botões e chamadas não relacionadas.
5. Validar no MAME com inversão individual ligada/desligada e verificar que o FFB continua funcional.

Não substituir o proxy atual por uma DLL incompleta: isso pode remover o suporte LUT/FFB existente ou impedir o jogo de iniciar.
