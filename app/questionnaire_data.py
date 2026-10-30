"""
questionnaire_data.py
Definições dos testes psicométricos, estímulos visuais, itens fenomenológicos e gabaritos.
Os gabaritos e critérios de pontuação permanecem estritamente no backend.
"""

# Módulo 1: Rastreio Fenomenológico (Escala Likert de 1 a 5)
FENOMENOLOGICO_ITEMS = [
    {
        "id": "fen_1",
        "category": "aprendizado",
        "title": "Padrão de Aprendizado e Hiperfoco",
        "question": "Quando se interessa por um assunto novo, você costuma ir das premissas básicas até a exaustão dos detalhes em poucos dias (hiperfoco autodidata)?",
        "options": [
            {"value": 1, "label": "Nunca / Nada a ver comigo"},
            {"value": 2, "label": "Raramente"},
            {"value": 3, "label": "Às vezes / Moderado"},
            {"value": 4, "label": "Frequentemente"},
            {"value": 5, "label": "Quase sempre / Descreve perfeitamente"}
        ]
    },
    {
        "id": "fen_2",
        "category": "aprendizado",
        "title": "Aversão à Redundância",
        "question": "Você sente incômodo e tédio quase físico quando precisa acompanhar explicações muito lentas, redundantes ou lineares de algo que já compreendeu intuitivamente?",
        "options": [
            {"value": 1, "label": "Nunca"},
            {"value": 2, "label": "Raramente"},
            {"value": 3, "label": "Às vezes"},
            {"value": 4, "label": "Frequentemente"},
            {"value": 5, "label": "Sempre / É extremamente desgastante"}
        ]
    },
    {
        "id": "fen_3",
        "category": "intelectual",
        "title": "Hiperexcitabilidade Intelectual",
        "question": "Você tem forte sensibilidade a inconsistências lógicas no discurso dos outros, a ponto de sentir um impulso quase incontrolável de questionar ou corrigir a premissa?",
        "options": [
            {"value": 1, "label": "Nunca"},
            {"value": 2, "label": "Raramente"},
            {"value": 3, "label": "Às vezes"},
            {"value": 4, "label": "Frequentemente"},
            {"value": 5, "label": "Quase sempre"}
        ]
    },
    {
        "id": "fen_4",
        "category": "intelectual",
        "title": "Busca por Causa Raiz e Complexidade",
        "question": "Sente prazer intrínseco pela complexidade, busca compulsiva por compreender a causa raiz de sistemas e desconstrução de premissas óbvias?",
        "options": [
            {"value": 1, "label": "Discordo totalmente"},
            {"value": 2, "label": "Discordo"},
            {"value": 3, "label": "Neutro"},
            {"value": 4, "label": "Concordo"},
            {"value": 5, "label": "Concordo totalmente"}
        ]
    },
    {
        "id": "fen_5",
        "category": "emocional",
        "title": "Hiperexcitabilidade Emocional & Senso de Justiça",
        "question": "Crises existenciais, preocupação profunda com o sentido da vida ou sentimento agudo e doloroso de justiça surgiram muito cedo na sua trajetória?",
        "options": [
            {"value": 1, "label": "Não reconheço em mim"},
            {"value": 2, "label": "Pouco presente"},
            {"value": 3, "label": "Moderado"},
            {"value": 4, "label": "Marcante desde a infância/juventude"},
            {"value": 5, "label": "Intenso e central na minha vida"}
        ]
    },
    {
        "id": "fen_6",
        "category": "imaginativa",
        "title": "Hiperexcitabilidade Imaginativa",
        "question": "Apresenta pensamento visual vívido, metáforas automáticas e facilidade para projetar múltiplos cenários hipotéticos ou futuros alternativos em segundos?",
        "options": [
            {"value": 1, "label": "Raramente penso assim"},
            {"value": 2, "label": "Ocasionalmente"},
            {"value": 3, "label": "Com frequência moderada"},
            {"value": 4, "label": "Muito frequentemente"},
            {"value": 5, "label": "É o meu padrão mental constante"}
        ]
    },
    {
        "id": "fen_7",
        "category": "sensorial",
        "title": "Hiperexcitabilidade Sensorial",
        "question": "Estímulos sensoriais (ruídos repetitivos específicos, iluminação excessiva, texturas de tecidos ou cheiros) drenam sua energia muito mais rápido do que a exigência mental propriamente dita?",
        "options": [
            {"value": 1, "label": "Não me afetam"},
            {"value": 2, "label": "Afetam muito pouco"},
            {"value": 3, "label": "Incômodo moderado"},
            {"value": 4, "label": "Incomodam bastante"},
            {"value": 5, "label": "Causam sobrecarga sensorial nítida"}
        ]
    },
    {
        "id": "fen_8",
        "category": "psicomotora",
        "title": "Hiperexcitabilidade Psicomotora",
        "question": "Apresenta alto nível de energia mental/física, fala rápida, dificuldade crônica para 'desligar' o cérebro à noite e necessidade de movimentação?",
        "options": [
            {"value": 1, "label": "Discordo totalmente"},
            {"value": 2, "label": "Discordo"},
            {"value": 3, "label": "Neutro"},
            {"value": 4, "label": "Concordo"},
            {"value": 5, "label": "Concordo totalmente"}
        ]
    },
    {
        "id": "fen_9",
        "category": "discronia",
        "title": "Assincronia do Desenvolvimento (Discronia)",
        "question": "O seu avanço cognitivo e intelectual costuma andar muito à frente do seu amadurecimento emocional, motor ou da tolerância social com os outros?",
        "options": [
            {"value": 1, "label": "Nunca percebi essa distância"},
            {"value": 2, "label": "Raramente"},
            {"value": 3, "label": "Às vezes"},
            {"value": 4, "label": "Frequentemente causa atritos internos"},
            {"value": 5, "label": "Sempre vivenciei esse descompasso"}
        ]
    },
    {
        "id": "fen_10",
        "category": "paralisia",
        "title": "Paralisia por Análise e Perfeccionismo",
        "question": "Como seu cérebro antecipa dezenas de cenários de falha e variáveis que a maioria ignora, iniciar ou finalizar um projeto é frequentemente bloqueado pela busca do padrão ótimo?",
        "options": [
            {"value": 1, "label": "Não sofro com isso"},
            {"value": 2, "label": "Raramente"},
            {"value": 3, "label": "Às vezes"},
            {"value": 4, "label": "Frequentemente me sabota"},
            {"value": 5, "label": "É um dos meus maiores gargalos operacionais"}
        ]
    },
    {
        "id": "fen_11",
        "category": "comunicacao",
        "title": "Sensação de Descompasso na Verbalização",
        "question": "Você costuma ter a sensação de que 'já sabe a resposta ou o desfecho', mas sente cansaço ou sobrecarga para verbalizar todas as etapas intermediárias passo a passo para as outras pessoas?",
        "options": [
            {"value": 1, "label": "Não sinto isso"},
            {"value": 2, "label": "Raramente"},
            {"value": 3, "label": "Às vezes"},
            {"value": 4, "label": "Frequentemente"},
            {"value": 5, "label": "Quase sempre me sinto falando em outra frequência"}
        ]
    },
    {
        "id": "fen_trap",
        "category": "validade_pvt",
        "title": "Controle de Foco e Validade (PVT)",
        "question": "Para garantir a fidedignidade da testagem e comprovar que este enunciado está sendo lido com atenção, selecione a opção número 1 (Discordo Totalmente).",
        "options": [
            {"value": 1, "label": "1 - Discordo Totalmente"},
            {"value": 2, "label": "2 - Discordo"},
            {"value": 3, "label": "3 - Neutro"},
            {"value": 4, "label": "4 - Concordo"},
            {"value": 5, "label": "5 - Concordo Totalmente"}
        ]
    }
]

# Módulo 2: Raciocínio Fluido (Gf) - Matrizes Progressivas Visuais
# Cada matriz define um padrão lógico paramétrico e alternativas
MATRIZES_ITEMS = [
    {
        "id": "mat_1",
        "difficulty": 1,
        "rule_type": "Progressão de preenchimento (Escala básica)",
        "description": "Observe o padrão de preenchimento dos círculos na linha e identifique o elemento ausente no canto inferior direito.",
        "grid": [
            [{"type": "circle", "fill": 25}, {"type": "circle", "fill": 50}, {"type": "circle", "fill": 75}],
            [{"type": "circle", "fill": 50}, {"type": "circle", "fill": 75}, {"type": "circle", "fill": 100}],
            [{"type": "circle", "fill": 75}, {"type": "circle", "fill": 100}, {"type": "missing"}]
        ],
        "options": [
            {"id": "A", "item": {"type": "circle", "fill": 50}},
            {"id": "B", "item": {"type": "circle", "fill": 100}},
            {"id": "C", "item": {"type": "circle", "fill": 125, "special": "full_double"}}, # Correta
            {"id": "D", "item": {"type": "square", "fill": 100}}
        ],
        "correct_id": "C"
    },
    {
        "id": "mat_2",
        "difficulty": 2,
        "rule_type": "Rotação horária de 45 graus",
        "description": "Identifique a orientação da seta que completa a sequência geométrica.",
        "grid": [
            [{"type": "arrow", "rot": 0}, {"type": "arrow", "rot": 45}, {"type": "arrow", "rot": 90}],
            [{"type": "arrow", "rot": 90}, {"type": "arrow", "rot": 135}, {"type": "arrow", "rot": 180}],
            [{"type": "arrow", "rot": 180}, {"type": "arrow", "rot": 225}, {"type": "missing"}]
        ],
        "options": [
            {"id": "A", "item": {"type": "arrow", "rot": 270}}, # Correta
            {"id": "B", "item": {"type": "arrow", "rot": 315}},
            {"id": "C", "item": {"type": "arrow", "rot": 180}},
            {"id": "D", "item": {"type": "arrow", "rot": 0}}
        ],
        "correct_id": "A"
    },
    {
        "id": "mat_3",
        "difficulty": 3,
        "rule_type": "Adição / Subtração booleana (XOR de segmentos)",
        "description": "As linhas da terceira coluna resultam da superposição lógica (XOR) das duas primeiras colunas.",
        "grid": [
            [{"type": "cross_h"}, {"type": "cross_v"}, {"type": "cross_plus"}],
            [{"type": "diag_l"}, {"type": "diag_r"}, {"type": "cross_x"}],
            [{"type": "box_open_top"}, {"type": "line_top"}, {"type": "missing"}]
        ],
        "options": [
            {"id": "A", "item": {"type": "box_open_bottom"}},
            {"id": "B", "item": {"type": "box_closed"}}, # Correta
            {"id": "C", "item": {"type": "line_v"}},
            {"id": "D", "item": {"type": "cross_plus"}}
        ],
        "correct_id": "B"
    },
    {
        "id": "mat_4",
        "difficulty": 4,
        "rule_type": "Distribuição de 3 formas x 3 texturas",
        "description": "Cada linha e cada coluna contém obrigatoriamente 3 formas distintas e 3 preenchimentos distintos.",
        "grid": [
            [{"type": "shape", "s": "circle", "p": "solid"}, {"type": "shape", "s": "square", "p": "striped"}, {"type": "shape", "s": "triangle", "p": "outline"}],
            [{"type": "shape", "s": "square", "p": "outline"}, {"type": "shape", "s": "triangle", "p": "solid"}, {"type": "shape", "s": "circle", "p": "striped"}],
            [{"type": "shape", "s": "triangle", "p": "striped"}, {"type": "shape", "s": "circle", "p": "outline"}, {"type": "missing"}]
        ],
        "options": [
            {"id": "A", "item": {"type": "shape", "s": "square", "p": "striped"}},
            {"id": "B", "item": {"type": "shape", "s": "square", "p": "solid"}}, # Correta: quadrado + sólido
            {"id": "C", "item": {"type": "shape", "s": "circle", "p": "solid"}},
            {"id": "D", "item": {"type": "shape", "s": "triangle", "p": "outline"}}
        ],
        "correct_id": "B"
    },
    {
        "id": "mat_5",
        "difficulty": 5,
        "rule_type": "Progressão bidirecional e inversão de elementos concêntricos",
        "description": "Analise a evolução dos anéis e núcleos concêntricos ao longo da matriz.",
        "grid": [
            [{"type": "concentric", "rings": 1, "dot": False}, {"type": "concentric", "rings": 2, "dot": False}, {"type": "concentric", "rings": 3, "dot": False}],
            [{"type": "concentric", "rings": 1, "dot": True}, {"type": "concentric", "rings": 2, "dot": True}, {"type": "concentric", "rings": 3, "dot": True}],
            [{"type": "concentric", "rings": 2, "dot": True}, {"type": "concentric", "rings": 3, "dot": True}, {"type": "missing"}]
        ],
        "options": [
            {"id": "A", "item": {"type": "concentric", "rings": 4, "dot": True}}, # Correta
            {"id": "B", "item": {"type": "concentric", "rings": 3, "dot": False}},
            {"id": "C", "item": {"type": "concentric", "rings": 2, "dot": False}},
            {"id": "D", "item": {"type": "concentric", "rings": 4, "dot": False}}
        ],
        "correct_id": "A"
    },
    {
        "id": "mat_6",
        "difficulty": 5,
        "rule_type": "Armadilha de Controle de Atenção / PVT",
        "description": "Identifique a opção que possui exatamente o mesmo desenho que o elemento central da linha superior.",
        "grid": [
            [{"type": "shape", "s": "star", "p": "solid"}, {"type": "shape", "s": "diamond", "p": "outline"}, {"type": "shape", "s": "hexagon", "p": "striped"}],
            [{"type": "shape", "s": "hexagon", "p": "striped"}, {"type": "shape", "s": "diamond", "p": "outline"}, {"type": "shape", "s": "star", "p": "solid"}],
            [{"type": "shape", "s": "diamond", "p": "outline"}, {"type": "shape", "s": "diamond", "p": "outline"}, {"type": "missing"}]
        ],
        "options": [
            {"id": "A", "item": {"type": "shape", "s": "diamond", "p": "outline"}}, # Correta (muito evidente para checar malingering)
            {"id": "B", "item": {"type": "shape", "s": "square", "p": "outline"}},
            {"id": "C", "item": {"type": "shape", "s": "circle", "p": "solid"}},
            {"id": "D", "item": {"type": "shape", "s": "triangle", "p": "outline"}}
        ],
        "correct_id": "A"
    }
]

# Módulo 3: Corsi Blocks (Memória Operacional - Gwm)
CORSI_CONFIG = {
    "num_blocks": 9,
    "practice_sequence": [2, 6, 8],
    "test_sequences": [
        {"level": 1, "sequence": [1, 5, 9], "span": 3},
        {"level": 2, "sequence": [3, 7, 2, 8], "span": 4},
        {"level": 3, "sequence": [9, 1, 4, 6, 2], "span": 5},
        {"level": 4, "sequence": [5, 3, 8, 2, 7, 4], "span": 6},
        {"level": 5, "sequence": [7, 1, 9, 3, 5, 8, 2], "span": 7},
        {"level": 6, "sequence": [4, 8, 2, 9, 1, 6, 3, 7], "span": 8}
    ]
}

# Módulo 4: Velocidade de Processamento (Gs) - Pareamento e Cancelamento
VELOCIDADE_ITEMS = [
    {"id": f"vel_{i}", "pair": p, "is_match": p[0] == p[1]}
    for i, p in enumerate([
        ("▲", "▲"), ("◆", "◇"), ("●", "●"), ("■", "▲"), ("★", "★"),
        ("✚", "✖"), ("◈", "◈"), ("⬟", "⬟"), ("⬢", "⬡"), ("◉", "◉"),
        ("▲", "▼"), ("◐", "◐"), ("◑", "◐"), ("■", "■"), ("✦", "✦"),
        ("✪", "✪"), ("⬣", "⬢"), ("▶", "▶"), ("◀", "▶"), ("▼", "▼")
    ], 1)
]

# Módulo 5: Adaptação Digital WCST (Wisconsin Card Sorting Test) - Flexibilidade Cognitiva
# 4 Cartas Âncora padrão do teste:
# 1 = Um triângulo vermelho
# 2 = Duas estrelas verdes
# 3 = Três cruzes amarelas
# 4 = Quatro círculos azuis
WCST_ANCHORS = [
    {"anchor_id": 1, "count": 1, "shape": "triangle", "color": "red"},
    {"anchor_id": 2, "count": 2, "shape": "star", "color": "green"},
    {"anchor_id": 3, "count": 3, "shape": "cross", "color": "yellow"},
    {"anchor_id": 4, "count": 4, "shape": "circle", "color": "blue"}
]

# Sequência de cartas a serem classificadas:
WCST_TRIALS = [
    {"trial": 1, "card": {"count": 1, "shape": "circle", "color": "red"}},
    {"trial": 2, "card": {"count": 2, "shape": "triangle", "color": "blue"}},
    {"trial": 3, "card": {"count": 3, "shape": "circle", "color": "red"}},
    {"trial": 4, "card": {"count": 4, "shape": "star", "color": "yellow"}},
    {"trial": 5, "card": {"count": 1, "shape": "star", "color": "red"}},
    {"trial": 6, "card": {"count": 2, "shape": "cross", "color": "green"}},
    {"trial": 7, "card": {"count": 3, "shape": "star", "color": "blue"}},
    {"trial": 8, "card": {"count": 4, "shape": "triangle", "color": "yellow"}},
    {"trial": 9, "card": {"count": 1, "shape": "circle", "color": "green"}},
    {"trial": 10, "card": {"count": 2, "shape": "circle", "color": "yellow"}},
    {"trial": 11, "card": {"count": 3, "shape": "triangle", "color": "red"}},
    {"trial": 12, "card": {"count": 4, "shape": "cross", "color": "green"}},
    {"trial": 13, "card": {"count": 1, "shape": "cross", "color": "blue"}},
    {"trial": 14, "card": {"count": 2, "shape": "star", "color": "red"}},
    {"trial": 15, "card": {"count": 3, "shape": "circle", "color": "yellow"}},
    {"trial": 16, "card": {"count": 4, "shape": "circle", "color": "red"}},
    {"trial": 17, "card": {"count": 1, "shape": "triangle", "color": "green"}},
    {"trial": 18, "card": {"count": 2, "shape": "cross", "color": "blue"}},
]

# Regras programadas: Primeiras 6 rodadas -> "color"; Próximas 6 -> "shape"; Próximas 6 -> "count"
WCST_RULE_SCHEDULE = [
    {"start": 1, "end": 6, "rule": "color"},
    {"start": 7, "end": 12, "rule": "shape"},
    {"start": 13, "end": 18, "rule": "count"}
]

# Módulo 6: Pensamento Divergente e Associação Remota (RAT)
ASSOCIACAO_ITEMS = [
    {
        "id": "rat_1",
        "words": ["Cottage", "Suíço", "Bolo"],
        "accepted_answers": ["queijo", "de queijo"],
        "hint": "Tipo de alimento/ingrediente comum"
    },
    {
        "id": "rat_2",
        "words": ["Mar", "Sal", "Gota"],
        "accepted_answers": ["água", "agua"],
        "hint": "Elemento líquido universal"
    },
    {
        "id": "rat_3",
        "words": ["Chave", "Mestre", "Cofre"],
        "accepted_answers": ["segredo", "fechadura", "código", "codigo"],
        "hint": "Conceito de segurança ou acesso"
    },
    {
        "id": "rat_4",
        "words": ["Noite", "Estrela", "Queda"],
        "accepted_answers": ["cadente", "céu", "ceu"],
        "hint": "Fenômeno astronômico ou visual"
    },
    {
        "id": "rat_5",
        "words": ["Sol", "Chuva", "Arco"],
        "accepted_answers": ["íris", "iris", "arco-íris", "arco-iris"],
        "hint": "Fenômeno óptico atmosférico"
    }
]

# Módulo 7: Desafios Metacognitivos Aprofundados (Transcritos do PDF)
METACOGNICAO_ITEMS = [
    {
        "id": "meta_1",
        "title": "1. Raciocínio Lógico e Metacognição (A Ilha dos Olhos Azuis)",
        "prompt": (
            "Em uma ilha vivem 100 lógicos perfeitos. Todos têm olhos azuis, mas ninguém sabe a cor dos próprios olhos "
            "e não há espelhos nem superfícies reflexivas. Na ilha existe uma lei rigorosa: qualquer pessoa que descubra "
            "com certeza matemática absoluta que tem olhos azuis deve deixar a ilha em silêncio no mesmo dia à meia-noite. "
            "Ninguém jamais fala sobre a cor dos olhos de ninguém.\n\n"
            "Certo dia, um visitante estrangeiro chega e declara publicamente a todos: 'Pelo menos um de vocês tem olhos azuis.'\n\n"
            "O que acontece depois dessa declaração, e por quê?"
        ),
        "options": [
            {
                "id": "A",
                "label": "Nada acontece, porque todos já viam 99 pessoas de olhos azuis e a informação não acrescentou nada de novo."
            },
            {
                "id": "B",
                "label": "Todos os 100 lógicos deixam a ilha juntos exatamente na 100ª noite à meia-noite, por indução lógica sobre conhecimento comum (common knowledge)."
            },
            {
                "id": "C",
                "label": "Apenas um lógico sai na primeira noite, e os outros 99 permanecem."
            },
            {
                "id": "D",
                "label": "Todos saem imediatamente na primeira noite à meia-noite."
            }
        ],
        "correct_id": "B",
        "rationale_optimal": (
            "A declaração do visitante cria 'conhecimento comum' (todos sabem que todos sabem...). "
            "Para N=1, o único sairia no dia 1. Para N=2, vendo 1 de olhos azuis que não saiu no dia 1, ambos deduzem no dia 2. "
            "Por indução matemática rigorosa, com N=100 lógicos perfeitos, todos saem simultaneamente na 100ª noite."
        )
    },
    {
        "id": "meta_2",
        "title": "2. Pensamento Lateral e Modelagem Matemática (As Duas Cordas de 45 minutos)",
        "prompt": (
            "Você tem duas cordas de materiais irregulares. Cada uma leva exatamente 60 minutos para queimar de uma ponta à outra. "
            "No entanto, elas não queimam em ritmo constante (por exemplo, metade do comprimento de uma corda pode queimar em 10 minutos, "
            "e a outra metade nos 50 minutos restantes).\n\n"
            "Apenas com as duas cordas e fósforos, como você consegue medir com exatidão um intervalo de 45 minutos?"
        ),
        "options": [
            {
                "id": "A",
                "label": "Corta-se a segunda corda em três pedaços iguais de 15 minutos e acende-se uma ponta."
            },
            {
                "id": "B",
                "label": "Acende-se a corda 1 pelas duas pontas simultaneamente e a corda 2 por apenas uma ponta. Quando a corda 1 terminar (30 min), acende-se a outra ponta da corda 2 (queima em mais 15 min, totalizando 45 min)."
            },
            {
                "id": "C",
                "label": "Acendem-se as duas cordas ao mesmo tempo por ambas as pontas e calcula-se a média aritmética das durações."
            },
            {
                "id": "D",
                "label": "Dobra-se a corda ao meio para marcar 30 minutos e dobra-se novamente para 15 minutos."
            }
        ],
        "correct_id": "B",
        "rationale_optimal": (
            "Como a queima é não-linear no espaço, cortar ou dobrar é inválido. A única invariante temporal é que acender "
            "uma corda de 60 min por AMBAS as pontas força o ponto de encontro a durar exatamente 30 min. Ao mesmo tempo, "
            "a corda 2 queima por uma ponta (restando 30 min de queima normal). Quando a corda 1 se extingue aos 30 min, "
            "acender a outra ponta da corda 2 faz o restante queimar na metade do tempo (15 min). Total: 30 + 15 = 45 min exatos."
        )
    },
    {
        "id": "meta_3",
        "title": "3. Analogia Estrutural e Pensamento em Rede",
        "prompt": (
            "Analise a seguinte relação estrutural:\n"
            "'Átomos estão para cristais assim como as notas musicais estão para um acorde harmônico.'\n\n"
            "Identifique qual é o princípio invariante (a regra abstrata comum) que rege ambas as relações "
            "e formule/selecione um terceiro sistema de domínio completamente diferente que siga exatamente essa mesma regra:"
        ),
        "options": [
            {
                "id": "A",
                "label": "Princípio da Simetria Estática: objetos com mesmo peso molecular se atraem, como notas na mesma oitava."
            },
            {
                "id": "B",
                "label": "Princípio da Emergência de Ordem Superior: unidades discretas fundamentais (átomos/notas), combinadas segundo regras de proporção/ressonância geométrica ou ondulatória, geram propriedades qualitativas inteiramente novas e emergentes (como fonemas/morfemas gerando linguagem com significado, ou aminoácidos gerando proteínas funcionais)."
            },
            {
                "id": "C",
                "label": "Princípio da Acumulação Quantitativa: quanto mais elementos forem adicionados, maior a densidade espacial do objeto resultante."
            },
            {
                "id": "D",
                "label": "Princípio da Dissolução Entrópica: elementos simples tendem naturalmente à desordem e ruído caótico."
            }
        ],
        "correct_id": "B",
        "rationale_optimal": (
            "O princípio invariante é a emergência de estrutura a partir de unidades elementares sob regras combinatórias rigorosas. "
            "Nem o átomo isolado tem a clivagem do cristal, nem a nota isolada tem a harmonia/tensão do acorde. "
            "Exemplos equivalentes: Aminoácidos -> Dobramento de Proteína terciária funcional; Fonemas/Letras -> Semântica/Sentido do Discurso; "
            "Transistores/Portas lógicas -> Algoritmo/Software computacional."
        )
    }
]
