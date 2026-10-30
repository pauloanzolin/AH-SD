# Plataforma Psicométrica Computadorizada - Arquitetura da Mente Superdotada (AH/SD)

Sistema completo para modelagem, aplicação e diagnóstico neurocognitivo da mente com Altas Habilidades ou Superdotação (AH/SD), desenvolvido com base nos parâmetros da **Psicometria**, da **Neuropsicologia Computacional** e nas diretrizes internacionais de testagem (ITC / APA).

O projeto é estruturado para execução em **Docker** com suporte direto a proxy reverso (**Nginx**), persistência de banco de dados em volume local e organização hierárquica por **Projetos e Participantes**.

---

## 🚀 Como Executar com Docker (Recomendado)

O projeto está pronto para subir com um único comando utilizando o Docker Compose:

### 1. Subir o container:
```bash
docker compose up -d --build
```

O container subirá na porta `8000`. O volume `./data` será criado automaticamente na raiz do projeto para persistir o banco de dados SQLite (`./data/ahsd.db`).

### 2. Acessar a aplicação:
Abra no seu navegador:
```
http://localhost:8000
```

### 3. Verificar status e logs:
```bash
# Ver logs do container
docker compose logs -f

# Parar o container mantendo os dados salvos
docker compose down
```

---

## 🌐 Como Integrar com Nginx (Proxy Reverso)

Para disponibilizar a aplicação em um servidor web com seu próprio domínio e certificado SSL através do Nginx, utilize o arquivo modelo fornecido em [`nginx.conf.example`](./nginx.conf.example).

Basta copiar ou incluir as diretivas no bloco do seu site no Nginx:

```nginx
upstream ahsd_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name seu-dominio.com.br;

    location / {
        proxy_pass http://ahsd_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 💻 Como Executar Localmente (Sem Docker)

Caso queira executar em seu ambiente Python diretamente:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Iniciar o servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📁 Estrutura de Projetos e Participantes

A aplicação foi projetada para salvar todas as avaliações de forma organizada e rastreável:

1. **Projetos / Campanhas:**
   - Você pode criar áreas temáticas como `Teste 1`, `Piloto AH/SD 2026` ou `Avaliação Familiar`.
2. **Participantes & Testes Vinculados:**
   - Dentro de qualquer projeto, clique em **+ Novo Teste / Participante** e informe o nome (ex.: `Paulo`), idade e escolaridade.
   - O sistema cria a sessão e abre o ambiente de teste diretamente.
3. **Persistência Completa:**
   - É possível iniciar, pausar e retomar o teste a qualquer momento.
   - Quando o teste é concluído, o laudo com gráficos, escores Z, percentis e parecer qualitativo fica congelado e acessível para consultas futuras no painel.

---

## 🧠 Domínios Neurocognitivos Mapeados (Conforme PDF)

O teste abrangerá os 7 módulos científicos descritos na conversa:

1. **Rastreio Qualitativo de Padrões e Vivências (Dabrowski & Estilo Cognitivo):**
   - Mensuração das 5 Hiperexcitabilidades (Intelectual, Emocional, Imaginativa, Sensorial, Psicomotora);
   - Investigação de hiperfoco autodidata, tédio com explicações redundantes, discronia do desenvolvimento, paralisia por análise e descompasso na verbalização linear;
   - Inclui item armadilha de controle de atenção (SVT/PVT).

2. **Raciocínio Fluido (Gf) - Matrizes Progressivas Não-Verbais:**
   - 8 matrizes progressivas visuais em SVG (rotação, superposição lógica XOR/AND e padrões concêntricos);
   - Registro de precisão e latência em milissegundos via `performance.now()`.

3. **Memória Operacional (Gwm) - Corsi Blocks:**
   - Tarefa de span visuoespacial digital com sequências de 3 a 8 blocos ativamente manipulados em tempo real.

4. **Velocidade de Processamento (Gs) - Discriminação Rápida:**
   - Tarefa de pareamento rápido e cancelamento de símbolos com cronometragem precisa.

5. **Flexibilidade Cognitiva - Adaptação Digital WCST (Wisconsin Card Sorting Test):**
   - Classificação sob regras implícitas (Cor, Forma, Quantidade) com feedback imediato e mudança oculta de regra para medir erros perseverativos.

6. **Pensamento Divergente / Criatividade - Teste de Associação Remota (RAT):**
   - Tríades conceituais para resgate de conexões semânticas em rede.

7. **Metacognição e Desafios Aprofundados da Conversa:**
   - *A Ilha dos Olhos Azuis* (indução matemática e conhecimento comum);
   - *As Duas Cordas de 45 minutos* (modelagem temporal não linear);
   - *A Analogia Estrutural Átomos/Cristais -> Notas/Acorde* (pensamento em rede e emergência de ordem superior).

---

## 🔒 Segurança, Fidedignidade e Deontologia

- **Isolamento de Gabarito:** Todas as chaves de resposta, critérios do WCST e fórmulas de ponderação rodam exclusivamente no backend.
- **Detecção de Anomalias:** O sistema detecta chutes excessivamente rápidos (<150ms), perdas de foco da janela (`blur` e troca de abas) e falhas em itens armadilha (malingering).
- **Laudo e Exportação:** O relatório exibe gráfico Radar de domínios, tabela com escores Z, T, percentis e estimativa da curva de Gauss de QI ($\mu=100, \sigma=15$), com layout amigável para impressão ou exportação em PDF (`Ctrl + P`).
