## Descricao das Alteracoes
Descreva de forma clara e concisa o que este Pull Request introduz, corrige ou melhora no piDots.

## Tipo de Alteracao
- [ ] Correcao de bug (`fix`)
- [ ] Nova funcionalidade (`feat`)
- [ ] Otimizacao de desempenho / reducao de RAM (`perf`)
- [ ] Atualizacao de documentacao (`docs`)
- [ ] Refatoracao sem quebra de comportamento (`refactor`)
- [ ] Ajuste em suites de testes (`test`)
- [ ] Manutencao de infraestrutura ou CI (`chore` / `ci`)

## Checklist de Conformidade Tecnica
- [ ] O codigo segue a padronizacao PEP 8 e possui tipagem completa (PEP 484 / Pydantic v2).
- [ ] Nao ha chamadas bloqueantes de I/O no event loop assincrono principal.
- [ ] O consumo de memoria RAM permanece dentro dos limites de borda (< 60 MB idle, < 150 MB pico).
- [ ] A regra inegociavel de **zero emojis** foi rigorosamente respeitada em todo o codigo, comentarios e documentacao.
- [ ] Todas as suites de testes automatizados locais foram executadas e aprovadas com 100% de sucesso (`scripts/test_phase1.py` a `scripts/test_phase5.py`).
- [ ] O teste de estresse de concorrencia foi executado com sucesso (`scripts/stress_test.py`).
- [ ] A documentacao correspondente foi atualizada em caso de novas funcionalidades ou alteracao de endpoints.
- [ ] Nenhuma credencial, segredo ou chave de API privada foi commitada.
