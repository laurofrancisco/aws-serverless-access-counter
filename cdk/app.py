#!/usr/bin/env python3
import aws_cdk as cdk
from stack import ContadorAcessosStack # Importa o arquivo stack.py

app = cdk.App()

# Instancia a sua infraestrutura
ContadorAcessosStack(app, "ContadorAcessosStack")

app.synth()