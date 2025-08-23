https://www2.camara.leg.br/transparencia/dados-abertos/dados-abertos-legislativo/webservices/deputados/deputados


```mermaid
erDiagram
    DEPUTADO {
        int ideCadastro PK
        string condicao
        string nome
        string nomeParlamentar
        string urlFoto
        string sexo
        string uf
        string partido FK
        string gabinete
        string anexo
        string fone
        string email
    }
    
    DETALHES_DEPUTADO {
        int ideCadastro PK, FK
        string nome
        string nomeParlamentar
        string partido FK
        string uf
        string urlFoto
        string condicao
        string anexo
        string fone
        string email
        int num_comissoes
        int num_periodos_exercicio
        int num_liderancas
    }
    
    PARTIDO {
        string idPartido PK
        string siglaPartido
        string nomePartido
        date dataCriacao
        date dataExtincao
    }
    
    DEPUTADO ||--o{ DETALHES_DEPUTADO : possui
    DEPUTADO }o--|| PARTIDO : pertence
    DETALHES_DEPUTADO }o--|| PARTIDO : pertence
```

Relações Principais:
DEPUTADO → DETALHES_DEPUTADO: Relação 1:1 através de ideCadastro

DEPUTADO → PARTIDO: Relação N:1 através de partido → siglaPartido

DETALHES_DEPUTADO → PARTIDO: Relação N:1 através de partido → siglaPartido