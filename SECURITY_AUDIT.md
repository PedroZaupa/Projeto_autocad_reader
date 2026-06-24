# SECURITY AUDIT — Projeto_autocad_reader

**Data:** 2026-06-24  
**Auditor:** Claude Code (automatizado)  
**Repositório:** https://github.com/PedroZaupa/Projeto_autocad_reader  

---

## ⚠️ AÇÃO IMEDIATA NECESSÁRIA

### 1. Repositório PÚBLICO
O repositório está **público**. Segredos já foram expostos. Execute imediatamente:

```bash
gh repo edit PedroZaupa/Projeto_autocad_reader --visibility private
```

> **Aguardando confirmação** — não executado automaticamente.

### 2. Rotacionar/Revogar Credenciais Imediatamente
As seguintes chaves foram encontradas em `.env` files versionados em múltiplas branches.
**Os valores já estão públicos no GitHub — a limpeza do histórico NÃO revoga credenciais. Revogue agora.**

| Variável          | Branches Afetadas                                                      | Serviço           |
|-------------------|------------------------------------------------------------------------|-------------------|
| `OPENAI_API_KEY`  | `develop`, `origin/new-feutures`, `origin/test-openIa`, `origin/feuture-memorial` | OpenAI           |
| `GOOGLE_API_KEY`  | `origin/feuture-memorial`                                              | Google APIs       |

**Ações:**
- Revogar `OPENAI_API_KEY` em: https://platform.openai.com/api-keys
- Revogar `GOOGLE_API_KEY` em: https://console.cloud.google.com/apis/credentials
- Gerar novas chaves e armazenar **somente em `.env` local, nunca versionado**

---

## Branches

### Branches Locais
| Branch | Observação |
|--------|-----------|
| `develop` | Branch de trabalho ativa, contém `.env` versionado |
| `main` | Contém dados de cliente (DWG, BMP, XLSX, PDF, log) |

### Branches Remotas
| Branch Remota | Manter? | Motivo |
|---------------|---------|--------|
| `origin/main` | **SIM** | Branch principal |
| `origin/develop` | **EXCLUIR após limpeza** | Contém `.env`, dados de cliente |
| `origin/feuture-memorial` | **EXCLUIR após limpeza** | Contém `.env` raiz + DOCX + CSVs |
| `origin/new-feutures` | **EXCLUIR após limpeza** | Contém `.env`, dados de cliente |
| `origin/test-openIa` | **EXCLUIR após limpeza** | Contém `.env`, dados de cliente |

---

## Arquivos Sensíveis por Branch

### `develop` (local)
- `src/extrator/.env` — **SEGREDO: OPENAI_API_KEY, GOOGLE_API_KEY**
- `output/Projeto Urbanistico - Lote 02-03-04 - 04-08-25_resumo.json` — dado gerado de cliente
- `output/json/Projeto Urbanistico - Lote 02-03-04 - 04-08-25_tabelas_finais.json` — dado gerado de cliente

### `main` (local / `origin/main`)
- `Projeto Urbanistico teste/Projeto Urbanistico - Lote 02-03-04 - 04-08-25.bmp` — imagem cliente (4.8 MB)
- `Projeto Urbanistico teste/Projeto Urbanistico - Lote 02-03-04 - 04-08-25.dwg` — arquivo DWG cliente (2.4 MB)
- `Projeto Urbanistico teste/Projeto Urbanistico - Lote 02-03-04 - 04-08-25.xlsx` — planilha cliente (19 MB)
- `Projeto Urbanistico teste/plot.log` — log
- `data/pdfs/Projeto Urbanistico - Lote 02-03-04 - 04-08-25.pdf` — PDF cliente (1.5 MB)

### `origin/develop`
- Todos os de `main` +
- `data/_temp_dwg/...dwg` — DWG cliente
- `data/dxfs/...dxf` — DXF cliente (12.7 MB)
- `output/tabelas_extraidas/...xlsx` — output gerado
- `src/extrator/.env` — **SEGREDO**

### `origin/feuture-memorial`
- Todos os de `origin/develop` +
- `.env` **na raiz** — **SEGREDO: GOOGLE_API_KEY**
- `output/...memorial_final.docx` — documento gerado de cliente
- `output/csv/quadro_areas.csv` — dados de cliente
- `output/csv/tabelas_azimutes_coordenadas.csv` — dados de cliente

### `origin/new-feutures`
- Mesmos que `origin/develop` + `src/extrator/.env` (**SEGREDO**)

### `origin/test-openIa`
- Mesmos que `origin/develop` + `src/extrator/.env` (**SEGREDO**)

---

## Arquivos com Padrões de Segredo no Histórico (caminhos apenas)

Encontrados por `git grep` em todos os commits:

```
.env
scripts/ExtratorTopografia/.env
src/extrator/.env
```

Também foram encontrados arquivos Python que provavelmente **consomem** as chaves (não contêm valores em si, mas confirmam o uso):
```
src/extrator/core/analisador_ia.py
src/extrator/core/analisador_visual_ia.py
src/extrator/core/extrator_openai.py
src/extrator/core/gerador_ia.py
src/extrator/core/gerador_memorial_ia.py
src/extrator/core/gerador_memorial.py
scripts/ExtratorTopografia/extrator_openai.py
```

---

## Grandes Objetos no Histórico

| Tamanho | Arquivo |
|---------|---------|
| 19.3 MB | `Projeto Urbanistico teste/...xlsx` |
| 15.0 MB | `programs/poppler-25.07.0/Library/lib/poppler.lib` |
| 12.7 MB | `data/dxfs/...dxf` (9× no histórico) |
| 9.4 MB | `output/...png` |
| 7.4 MB | `programs/ODAfile/Qt6Gui.dll` |
| 7.3 MB | `programs/poppler-25.07.0/.../libcrypto-3-x64.dll` |
| 6.9 MB | `programs/ODAfile/TD_DbEntities_26.4_16.tx` |
| 6.2 MB | `programs/poppler-25.07.0/.../poppler.dll` |
| 6.0 MB | `imagens/pagina_1.png` |

> **Nota:** `programs/` contém binários de 3ª parte (Poppler, ODAfile) que não deveriam estar versionados. Considere usar instalação via script em vez de versionar binários.

---

## Arquivos/Paths para Remoção do Histórico (git-filter-repo)

Lista consolidada para uso na Tarefa 4:

```
.env
src/extrator/.env
scripts/ExtratorTopografia/.env
src/extrator/core/.env
data/
output/
outputs/
imagens/
Projeto Urbanistico teste/
programs/
*.pdf
*.docx
*.xlsx
*.xls
*.csv
*.dwg
*.dxf
*.bmp
*.png
*.log
*.zip
*.rar
*.7z
*.dll
*.lib
*.tx
```

---

## Plano de Comandos Destrutivos (Pendente de Confirmação)

### Passo A — Tornar repositório privado
```bash
gh repo edit PedroZaupa/Projeto_autocad_reader --visibility private
```

### Passo B — Limpeza do histórico (após backup mirror)
```bash
# 1. Clonar mirror (já existe: Projeto_autocad_reader-clean.git/)
cd ..
git clone --mirror git@github.com:PedroZaupa/Projeto_autocad_reader.git Projeto_autocad_reader-clean.git
cd Projeto_autocad_reader-clean.git

# 2. Executar filter-repo
git filter-repo --force \
  --invert-paths \
  --path .env \
  --path src/extrator/.env \
  --path scripts/ExtratorTopografia/.env \
  --path src/extrator/core/.env \
  --path data/ \
  --path output/ \
  --path outputs/ \
  --path imagens/ \
  --path "Projeto Urbanistico teste/" \
  --path programs/ \
  --path-glob '*.pdf' \
  --path-glob '*.docx' \
  --path-glob '*.xlsx' \
  --path-glob '*.xls' \
  --path-glob '*.csv' \
  --path-glob '*.dwg' \
  --path-glob '*.dxf' \
  --path-glob '*.bmp' \
  --path-glob '*.png' \
  --path-glob '*.log' \
  --path-glob '*.zip' \
  --path-glob '*.rar' \
  --path-glob '*.7z' \
  --path-glob '*.dll' \
  --path-glob '*.lib' \
  --path-glob '*.tx'
```

### Passo C — Validar limpeza (rodar auditoria novamente antes de push)

### Passo D — Push destrutivo (SOMENTE após validação)
```bash
cd Projeto_autocad_reader-clean.git
git push --force --mirror origin
```

### Passo E — Excluir branches remotas desnecessárias
```bash
git push origin --delete develop feuture-memorial new-feutures test-openIa
```

> Manter apenas `origin/main`.

---

## Validação Final

Execute após toda a limpeza:

```bash
git fetch --all --prune --tags
git branch -r
git ls-tree -r --name-only origin/main | grep -Ei '(^|/)(\.env($|\.)|data/|output/|outputs/|.*\.pdf$|.*\.docx$|.*\.xlsx?$|.*\.csv$|.*\.dwg$|.*\.dxf$|.*\.log$)' || echo 'OK: nada sensível na árvore da main'
git grep -I -l -E '(OPENAI|API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|DATABASE_URL|PRIVATE KEY|client_secret|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})' $(git rev-list --all) 2>/dev/null | sed -E 's/^[0-9a-f]{40}://' | sort -u || echo 'OK: nenhum segredo encontrado no histórico'
```

---

## Resumo de Riscos

| Risco | Severidade | Status |
|-------|-----------|--------|
| `OPENAI_API_KEY` exposta publicamente | CRÍTICO | **Revogar imediatamente** |
| `GOOGLE_API_KEY` exposta publicamente | CRÍTICO | **Revogar imediatamente** |
| Repositório público com dados de cliente | ALTO | Tornar privado |
| DWG/DXF/PDF/XLSX de cliente versionados | ALTO | Remover do histórico |
| Binários grandes (programs/) no histórico | MÉDIO | Remover do histórico |
| Ausência de `.gitignore` raiz | MÉDIO | **Corrigido nesta auditoria** |

---

> **AVISO FINAL:** Limpar o histórico Git **não invalida credenciais já expostas**. Mesmo após o `git filter-repo` e force-push, qualquer pessoa que tenha clonado ou feito fork do repositório pode ainda ter os valores. Revogue e regenere todas as chaves imediatamente, independentemente da limpeza do histórico.
