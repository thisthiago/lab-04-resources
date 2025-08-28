## 1) Criar a **Política** (permissions) a partir do JSON

1. Acesse **IAM > Políticas > Criar política**.
2. Aba **JSON** → cole a política abaixo → **Avançar** → dê um nome (ex.: `LambdaS3WriteAndLogs`) → **Criar política**.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowLambdaLogging",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Sid": "AllowS3WriteAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::dev-lab-02-us-east-2-landing/*"
    }
  ]
}
```

---

## 2) Criar a **Função (Role) do IAM** e anexar a política

1. Vá em **IAM > Funções (Roles) > Criar função**.
2. **Etapa 1 – Selecionar entidade confiável**: escolha **Serviço da AWS** e selecione **Lambda** → **Avançar**.
3. **Etapa 2 – Adicionar permissões**: pesquise e **marque** a política que você criou (`LambdaS3WriteAndLogs`).

   > (Opcional, boa prática): também pode anexar a gerenciada **AWSLambdaBasicExecutionRole**; se fizer isso, você pode remover o bloco de logs da política custom.
4. **Etapa 3 – Nomear, revisar e criar**: dê um nome (ex.: `role-lambda-partidos`) → **Criar função**.

---

## 3) Criar a **Função Lambda** usando a role acima

1. Acesse **Lambda > Create function**.
2. **Author from scratch**:

   * **Function name**: `lambda-partidos-salvar-s3`
   * **Runtime**: Python **3.11** (ou 3.12 se disponível)
3. Em **Permissions** → **Change default execution role** → **Use an existing role** → selecione **`role-lambda-partidos`** → **Create function**.

---

## 4) Código, handler e ajustes

1. Em **Code**, cole seu código no arquivo padrão `lambda_function.py`.
2. **Handler**: `lambda_function.lambda_handler`.
3. **Configuration > General configuration > Edit**:

   * **Timeout**: defina **60s** (seu `requests.get` usa timeout de 30s).
   * **Memory**: 256 MB (ou mais, se quiser folga).

## 5) Aumentar o timeout da Lambda no console da AWS:   
1. Navegue até: Lambda → Configurações → Geral → Tempo limite
2. Coloque algo mais seguro, como 30 segundos (ou até 60, se quiser margem).

