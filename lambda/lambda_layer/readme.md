## **Passo 1: Criar uma pasta para a layer**

No seu computador (ou em um EC2/Cloud9):

```bash
mkdir lambda_layer
cd lambda_layer
mkdir python
```

> Importante: para Lambda Layers em Python, a pasta que contém os pacotes deve se chamar `python`.

---

## **Passo 2: Instalar pacotes na pasta**

Use `pip` com o argumento `-t` (target) para instalar diretamente dentro da pasta `python`:

```bash
pip install pymongo dnspython -t python/
```

Isso vai criar dentro de `python/` todas as dependências necessárias.

---

## **Passo 3: Compactar a layer**

```bash
zip -r pymongo_layer.zip python
```

> O arquivo `pymongo_layer.zip` será o pacote da layer.

---

## **Passo 4: Criar a layer na AWS**

1. Vá para o console da AWS → **Lambda** → **Layers** → **Create layer**.
2. Nome: `pymongo-layer`
3. Upload do arquivo ZIP (`pymongo_layer.zip`)
4. Runtime: selecione o mesmo da sua Lambda, ex: **Python 3.9**
5. Criar

---

## **Passo 5: Anexar a layer à Lambda**

1. Vá na sua função Lambda → **Layers** → **Add a layer** → **Custom layers**
2. Selecione a layer criada (`pymongo-layer`) e a versão mais recente
3. Salve

---

