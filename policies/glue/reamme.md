-

# Criando a Role para AWS Glue no Console

## 1) Acesse o IAM

* Vá em **Console AWS → IAM**.
* No menu lateral, clique em **Roles** (funçõe).
* Clique em **Create role**.

---

## 2 Escolha o serviço confiável

* Em **Trusted entity type**, selecione **AWS Service**.
* Em **Use case**, escolha **Glue**.
* Clique em **Next**.

---

## 3️) Anexar permissões

Aqui você escolhe as **policies** que a role vai ter:

* Marque:

  * `AWSGlueServiceRole` (essencial para Glue funcionar)
  * `AmazonS3FullAccess` ou uma policy customizada só para os seus buckets 
  * `CloudWatchLogsFullAccess` (para enviar logs)

*(Se quiser ser mais restrito, pode criar policies específicas só para os buckets e logs necessários, em vez de full access.)*

Clique em **Next**.

---

## 4) Nomear a role

* Dê um nome, por exemplo:
  **`AWSGlueETLRole`**
* Opcional: escreva uma descrição (ex: *Role para executar jobs ETL no Glue Studio*).
* Clique em **Create role**.

