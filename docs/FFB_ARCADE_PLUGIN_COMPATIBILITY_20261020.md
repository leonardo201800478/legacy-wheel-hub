# Compatibilidade do Legacy Wheel Hub com o FFB Arcade Plugin — 2026-10-20

## Evidências coletadas no MAME do usuário

Arquivo observado:

`G:\\LaunchBox\\Emulators\\MAME\\dinput8.dll`

- Tamanho: 775.168 bytes.
- Data: 31/07/2024 20:09:31.
- Descrição do arquivo: `Force Feedback Plugin`.
- Versão: `2.0.0.53`.
- SHA-256 informado pelo usuário: `2443F1AF58743212B7FEEB408507B8EAF95922DA24F5966B66997898E90817B7`.
- `dumpbin /exports` mostrou 648 funções exportadas (644 nomes), incluindo `DirectInput8Create`, `DirectInputCreateA/W/Ex`, funções XInput, OpenGL, Direct3D e WinMM.

A versão e a descrição coincidem com o lançamento público **FFB Arcade Plugin 2.0.0.53**. O projeto upstream descreve um plugin de force feedback/rumble para jogos arcade e informa que a DLL principal pode ser renomeada para diferentes nomes de API, incluindo `dinput8.dll`. Isso explica por que a DLL encontrada exporta muitas funções não relacionadas diretamente ao DirectInput.

Referências:
- Repositório upstream: https://github.com/Boomslangnz/FFBArcadePlugin
- Releases: https://github.com/Boomslangnz/FFBArcadePlugin/releases
- Código upstream do wrapper DirectInput: https://github.com/Boomslangnz/FFBArcadePlugin/blob/master/DllMain.cpp

**Nota de verificação:** a identificação é fortemente sustentada pela versão, descrição e tabela de exports; o hash local ainda não foi comparado com um artefato oficial do release.

## Consequência para o Legacy Wheel Hub

A DLL compilada localmente pelo LWH tem 54.272 bytes e exporta apenas seis símbolos DirectInput. Ela não é compatível como substituta transparente da DLL multifuncional do FFB Arcade Plugin.

Não sobrescrever nem renomear a DLL original como parte de um teste automático. A simples troca pode remover a camada de force feedback do FFB Arcade Plugin e/ou quebrar APIs adicionais usadas pelo executável ou por outros componentes.

A proxy atual do LWH encaminha para o DirectInput do Windows em `%SystemRoot%\\System32\\dinput8.dll`; ela não encadeia automaticamente o FFB Arcade Plugin. Portanto, colocar a proxy do LWH na pasta do MAME não preservaria por si só o plugin existente.

## Plano de investigação seguro

1. Preservar a DLL original e registrar backup e hash antes de qualquer experimento.
2. Confirmar qual backend o MAME usa para os controles no perfil em questão. A lista de exports da DLL não prova que os eixos do MAME passam por `IDirectInputDevice8::GetDeviceState`.
3. Não assumir que encadear a DLL por um nome alternativo funcionará: o FFB Arcade Plugin seleciona seu caminho de hook conforme o nome/API da DLL, então renomeá-lo pode mudar o comportamento.
4. Avaliar uma integração explícita entre a inversão do LWH e o FFB Arcade Plugin, ou outro ponto de interceptação que preserve a implementação de FFB. Fazer isso somente após confirmar o caminho real de entrada e o contrato de inicialização do plugin.
5. Testar separadamente: entrada dos pedais, volante, botões e force feedback. Uma compilação bem-sucedida ou a presença de exports não demonstra compatibilidade em runtime.

## Estado

- [x] DLL original identificada por versão/descrição e exports.
- [x] Risco de substituição documentado.
- [ ] Backend de entrada efetivamente usado pelo MAME confirmado.
- [ ] Estratégia de integração validada sem perda de force feedback.
- [ ] Inversão de pedais validada no jogo.
