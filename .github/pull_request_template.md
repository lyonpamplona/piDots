## descricao das alteracoes
descreva de forma clara e concisa o que este pull request introduz, corrige ou melhora no pidots.

## tipo de alteracao
- [ ] correcao de bug (`fix`)
- [ ] nova funcionalidade (`feat`)
- [ ] otimizacao de desempenho / reducao de ram (`perf`)
- [ ] atualizacao de documentação (`docs`)
- [ ] refatoracao sem quebra de comportamento (`refactor`)
- [ ] ajuste em suites de testes (`test`)
- [ ] manutencao de infraestrutura ou ci (`chore` / `ci`)

## checklist de conformidade tecnica
- [ ] o codigo segue a padronizacao pep 8 e possui tipagem completa (pep 484 / pydantic v2).
- [ ] nao ha chamadas bloqueantes de i/o no event loop assincrono principal.
- [ ] o consumo de memória ram permanece dentro dos limites de borda (< 60 mb idle, < 150 mb pico).
- [ ] a regra inegociavel de **zero emojis** foi rigorosamente respeitada em todo o codigo, comentarios e documentação.
- [ ] todas as suites de testes automatizados locais foram executadas e aprovadas com 100% de sucesso (`scripts/test_phase1.py` a `scripts/test_phase5.py`).
- [ ] o teste de estresse de concorrencia foi executado com sucesso (`scripts/stress_test.py`).
- [ ] a documentação correspondente foi atualizada em caso de novas funcionalidades ou alteracao de endpoints.
- [ ] nenhuma credencial, segredo ou chave de api privada foi commitada.
