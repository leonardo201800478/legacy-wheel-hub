# Objetivos e roteiro técnico — paridade de funções do LGS 5 para o G27

**Data:** 2026-10-20  
**Escopo:** fork Legacy Wheel Hub, Logitech G27, Windows 11.  
**Estado:** requisitos do projeto definidos; as funcionalidades de inversão de pedais e atribuição de teclas ainda precisam de implementação e validação no jogo.

## Objetivos acordados

1. **Usar DLLs compatíveis com Windows 11.** Priorizar componentes em modo usuário e interfaces documentadas sempre que atendam ao requisito. Qualquer DLL precisa corresponder à arquitetura do processo-alvo (x86/x64), ter ciclo de instalação/remoção reversível e não comprometer a inicialização do jogo.
2. **Expandir o projeto original por meio do fork.** O fork existe para acrescentar funções que não estão disponíveis no projeto de origem; não se limitar a replicar a interface ou as capacidades atuais do original.
3. **Reproduzir no Legacy Wheel Hub as funções úteis do Logitech Gaming Software 5 (LGS 5) para o G27.** O objetivo é obter comportamento equivalente para o usuário, sem depender do LGS em tempo de execução.
4. **Implementar inversão real dos pedais.** As opções de acelerador, freio e embreagem precisam alterar os valores de eixo que o jogo efetivamente recebe. Salvar um booleano no perfil ou inverter apenas a representação na interface não conclui o requisito.
5. **Permitir atribuir teclas do teclado a botões do G27.** O usuário deve poder configurar um botão físico para gerar uma tecla, de modo semelhante ao recurso de atribuição do LGS 5. A implementação precisa definir como lidar com pressionamento, soltura, repetição e combinações de teclas.

## Requisitos negativos e restrições

- **O Hub deve funcionar sozinho.** Não editar XMLs do LGS, não exigir que o LGS esteja instalado ou em execução e não depender de uma configuração conjunta dos dois programas.
- **Não desativar Integridade da Memória, Isolamento do Núcleo ou outras proteções do Windows.**
- Não afirmar que uma opção está implementada até que exista uma prova reproduzível no aplicativo consumidor — para inversão, por exemplo, o painel de controle do Windows ou o MAME, conforme a camada escolhida.
- Preservar rotação, botões não remapeados e Force Feedback (FFB). Qualquer arquitetura que intercepte ou substitua o joystick deve explicar como o jogo continua enviando FFB ao G27 físico.
- Não instalar DLLs silenciosamente nem sobrescrever DLLs preexistentes do jogo. A instalação deve reconhecer DLLs de terceiros, oferecer backup/rollback e evitar alterar arquivos sem consentimento.
- Ferramentas de diagnóstico devem ser executadas manualmente; não adicionar captura contínua ou telemetria automática à aplicação final sem necessidade funcional.

## Arquitetura: separar os caminhos

O G27 envolve caminhos distintos, que não devem ser tratados como uma única função:

| Caminho | Responsabilidade | Observação |
|---|---|---|
| Configuração do volante/driver | Faixa de rotação, parâmetros específicos do dispositivo e outros ajustes suportados pelo driver | Investigar por recurso; não presumir que todas as opções do LGS sejam gravações de Registro ou comandos HID |
| Entrada do jogo | Eixos, pedais, botões e hat consumidos pelo MAME/jogo | A inversão precisa ocorrer neste caminho ou numa camada anterior efetivamente consumida pelo jogo |
| Mapeamento de teclas | Traduzir eventos de botões do G27 em eventos de teclado | Precisa emitir pressionar e soltar corretamente, sem tecla presa |
| Saída de Force Feedback | Efeitos enviados pelo jogo ao volante | Deve continuar chegando ao G27 físico, inclusive quando houver proxy ou dispositivo virtual |
| DLL por jogo | Possível ponto de compatibilidade/extensão no processo do jogo | A DLL `dinput8.dll` já usada para pós-processamento LUT é um caminho separado; não assumir que ela, por si só, modifica eixos ou mapeia teclas |

## Roteiro de implementação

### Fase 1 — inventário das DLLs e APIs disponíveis

- Inventariar as DLLs já incluídas no fork, suas arquiteturas (x86/x64), funções exportadas, origem, licença e comportamento no Windows 11.
- Identificar exatamente o que o proxy `dinput8.dll` atual faz e o que não faz.
- Determinar se a entrada do jogo é acessível por uma camada DirectInput interceptável em modo usuário e se o método é compatível com os jogos-alvo.
- Não concluir que uma DLL é compatível apenas porque pode ser copiada para a pasta do jogo: testar carregamento, encaminhamento de chamadas, inicialização e remoção.

### Fase 2 — inversão de pedais

- Definir a camada que altera os valores lidos pelo jogo. Comparar opções de proxy DirectInput em modo usuário e joystick virtual/roteamento de entrada.
- Avaliar a compatibilidade com x86/x64, Windows 11 e a integridade de memória ativada.
- Garantir que o jogo veja os pedais como eixos independentes quando aplicável e que o mapeamento seja configurável por perfil.
- Verificar o encaminhamento do FFB ao dispositivo físico antes de adotar uma solução baseada em joystick virtual.
- Criar testes para normalização de eixo, limites, sentido, centro, pedais combinados/separados e troca de perfil.
- Critério de aceite: alternar a inversão no Hub muda, de forma repetível, o sentido do eixo no consumidor sem precisar do LGS.

### Fase 3 — teclas nos botões do G27

- Criar um mapa por perfil: botão físico → tecla ou combinação de teclas.
- Separar eventos de key-down e key-up, liberando teclas quando o botão físico é solto, quando o perfil muda, quando o dispositivo desconecta e quando o Hub encerra.
- Definir comportamento de teclas modificadoras (Ctrl, Alt, Shift, Win), combinações, repetição e prevenção de tecla presa.
- Verificar as limitações de injeção de teclado no Windows, inclusive jogos elevados ou com mecanismos antitrapaça. Não prometer compatibilidade universal.
- Critério de aceite: o jogo/aplicativo-alvo recebe um pressionamento e uma soltura por acionamento do botão, conforme o mapeamento salvo, sem interferir nos demais botões.

### Fase 4 — validação e distribuição

- Validar em Windows 11 com as proteções de segurança ativadas.
- Testar jogos de 32 e 64 bits separadamente quando suportados.
- Fornecer instalação/desinstalação reversível, backups e diagnóstico manual.
- Documentar claramente as funções testadas, as limitações conhecidas e as dependências.

## Estado atual conhecido

- O Hub já salva opções de inversão no perfil, mas isso não significa que os eixos entregues ao jogo estejam invertidos.
- A função que editava XMLs do LGS foi removida. Isso está alinhado ao requisito de autonomia, mas não implementa a inversão por si só.
- O projeto já usa um proxy `dinput8.dll` para pós-processamento LUT. Esse mecanismo deve ser estudado como infraestrutura existente, mas sua capacidade de tratar entrada/teclas ainda não está comprovada.
- O XML de perfil do LGS 5 é referência observável de configuração, não especificação completa do protocolo interno entre LGS e driver.

## Regra para decisões técnicas

Para cada alternativa, registrar: API/camada modificada, arquitetura x86/x64, requisitos de instalação, compatibilidade com Windows 11 e Integridade da Memória, impacto no FFB, compatibilidade com o MAME e método de reversão. Distinguir sempre fatos observados, documentação oficial e hipóteses ainda não testadas.
