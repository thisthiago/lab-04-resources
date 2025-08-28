#### Configurar o MongoDB Atlas** 

Este é um erro muito comum\! Por padrão, o MongoDB Atlas bloqueia conexões de IPs desconhecidos. As funções Lambda não possuem um IP fixo, então a conexão falhará.

Para um teste rápido, libere o acesso de qualquer lugar:

1.  Acesse seu painel do **MongoDB Atlas**.
2.  No menu esquerdo, vá em **"Network Access"**.
3.  Clique em **"Add IP Address"**.
4.  Selecione **"Allow Access From Anywhere"**. Isso adicionará o IP `0.0.0.0/0`.
5.  Clique em **"Confirm"** e aguarde o status ficar "Active".


-----