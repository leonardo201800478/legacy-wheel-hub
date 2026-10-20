# Diagnóstico de entradas do Logitech G27 / DFGT

A ferramenta coleta evidências para mapear os eixos que o Windows expõe via SDL/Pygame, registrar pedais e botões e comparar os valores encontrados no XML do Logitech Gaming Software (LGS).

## Escopo e limitações

- Somente leitura: não altera registro, driver, firmware, configurações do volante ou XML do LGS.
- Enumera joysticks e registra eixos, botões e hats em CSV com timestamp.
- A calibração guiada tenta identificar qual eixo varia ao pressionar cada pedal e registra direção e amplitude.
- Opcionalmente lê XMLs LGS correspondentes ao executável informado e reporta Axis e Sign.
- Os valores coletados são os expostos pela API SDL/Pygame, não pacotes USB HID brutos.
- Encontrar Sign=-1 no XML não comprova que o perfil está ativo nem que o driver aplicou a alteração. O LGS pode selecionar perfil por executável; confirme o perfil ativo no cenário medido.
- A numeração SDL dos eixos não é necessariamente equivalente aos nomes de eixo no XML LGS, como R e Z.

## Requisitos

Windows 10/11 e Python 3.10+ recomendado. Instale:

~~~powershell
py -m pip install pygame-ce
~~~

Não é necessário executar como administrador.

## Uso

Na raiz do repositório:

~~~powershell
py tools\g27_input_diagnostics.py
~~~

Selecione um dispositivo específico quando houver mais de um:

~~~powershell
py tools\g27_input_diagnostics.py --device 0
~~~

Inspecione também os XMLs LGS de um executável:

~~~powershell
py tools\g27_input_diagnostics.py --exe "mame.exe"
~~~

Pule a calibração e comece a registrar:

~~~powershell
py tools\g27_input_diagnostics.py --skip-calibration --interval 0.01
~~~

Arquivos gerados por padrão em .\g27-diagnostics\:

- g27_input_<data>.csv: amostras de todos os eixos, botões e hats.
- g27_report_<data>.json: dispositivo, GUID, calibração, XML LGS encontrado e observações.

## Protocolo recomendado

1. Feche jogos e outros programas que possam interferir na entrada.
2. Execute a ferramenta e confirme nome e GUID do G27.
3. Durante a calibração, deixe os outros pedais soltos e pressione apenas o pedal solicitado.
4. Repita a calibração após inverter o pedal no Legacy Wheel Hub/LGS.
5. Compare os relatórios antes/depois: eixo alterado, direção, amplitude e estabilidade.
6. Para validar um perfil por jogo, confirme que o LGS realmente ativou o perfil desse executável. Não conclua que funcionou apenas porque o XML contém o valor esperado.
7. Revise CSV e JSON antes de compartilhar: GUIDs e caminhos locais podem revelar detalhes do computador.

## Interpretação

- Variação próxima de 1.0 costuma indicar grande movimento do eixo. Variação baixa pode significar que o pedal não foi movimentado, que outro eixo foi lido ou que a API não expõe o pedal como esperado.
- A direção registrada descreve o movimento observado; não declara, isoladamente, que o eixo está correto ou invertido.
- Se dois pedais movimentarem o mesmo eixo, repita o teste isoladamente e investigue o modo combinado de pedais/driver.

## Próxima etapa

Se SDL/Pygame não fornecer evidências suficientes, adicionar instrumentação Windows dedicada para enumerar dispositivos e eixos DirectInput, ler Raw Input/HID quando compatível e comparar entrada observada com Sign no perfil LGS. Essa etapa deve ser orientada pelos logs reais, sem presumir que índices SDL correspondam aos eixos LGS.


## Registro preliminar de calibração (relato do usuário, 2026-10-20)

Primeira execução reportada para o G27:

| Pedal | Eixo SDL (numeração exibida, iniciada em 1) | Variação | Direção observada |
|---|---:|---:|---|
| Acelerador | 2 | 2.000 | decreasing |
| Freio | 3 | 2.000 | decreasing |
| Embreagem | 5 | 2.000 | decreasing |

A amplitude 2.000 é compatível com uma excursão aproximada de +1 a -1 no eixo normalizado. Os três pedais foram detectados em eixos SDL distintos, todos decrescentes durante a pressão. Isso ainda não confirma que a inversão de um perfil LGS foi aplicada pelo driver, nem mapeia diretamente os eixos SDL aos nomes `R`/`Z` do XML.

A amostra final reportada foi `[-0.12796, 0.21429, 0.99997, -0.4679, 0.99997]`. Como ela é apenas um instante e não há informação sobre a posição de cada pedal nesse instante, não deve ser usada para concluir se os pedais estavam em repouso ou invertidos. O próximo passo é examinar o JSON completo (principalmente baseline, minimum e maximum de cada pedal) e o CSV, além do XML LGS correspondente ao executável testado. Este registro é evidência de uma execução reportada, não um teste independente reproduzido pelos mantenedores.
