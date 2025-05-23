<p align="center">
  <img src="https://raw.githubusercontent.com/sentinelzxofc/collected-dbs/logo.png" alt="Collected-DBs Logo" width="200"/>
</p>

<h1 align="center">Collected-DBs</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Versão-3.0.0-brightgreen" alt="Versão"/>
  <img src="https://img.shields.io/badge/Linguagem-Python-blue" alt="Linguagem"/>
  <img src="https://img.shields.io/badge/Plataforma-Termux-orange" alt="Plataforma"/>
  <img src="https://img.shields.io/badge/Foco-Captura_DB-red" alt="Foco"/>
</p>

<p align="center">
  <b>Uma ferramenta poderosa e focada para captura de bancos de dados expostos em websites</b><br>
  Desenvolvida especialmente para Termux sem necessidade de root
</p>

## 📋 Características

- **Foco Total em Captura de DB**: Ferramenta especializada em encontrar bancos de dados e arquivos de configuração expostos
- **Verificação Avançada**: Verifica mais de 300 caminhos comuns e obscuros para exposições de DB
- **Análise Inteligente**: Detecta credenciais, dumps SQL e outros dados sensíveis através de análise de conteúdo
- **Multithreading**: Verificação rápida e eficiente com processamento paralelo
- **Suporte a Proxy**: Compatível com HTTP, SOCKS4 e SOCKS5 para anonimato
- **Download Automático**: Baixa facilmente os arquivos expostos encontrados
- **Otimizado para Termux**: Funciona perfeitamente em dispositivos Android sem root

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/sentinelzxofc/collected-dbs.git

# Entre no diretório
cd collected-dbs

# Dê permissão de execução ao instalador
chmod +x install.sh

# Execute o instalador
./install.sh

# Execute o programa
python main.py
```

## 📱 Compatibilidade

- **Termux**: Totalmente compatível e otimizado
- **Android**: Não requer root
- **Linux**: Compatível com qualquer distribuição Linux

## 🔍 Como Usar

1. Inicie o programa com `python main.py`
2. Selecione a opção 1 para verificar exposição de DB
3. Digite a URL do website alvo (ex: exemplo.com ou https://exemplo.com)
4. Aguarde a verificação automática de todos os caminhos
5. Quando encontrar exposições, use a opção 2 para baixar os arquivos

<p align="center">
  <img src="https://raw.githubusercontent.com/sentinelzxofc/collected-dbs/main/assets/screenshot.png" alt="Screenshot" width="600"/>
</p>

## 🔧 Configuração de Proxy

Para usar com proxy:

1. Selecione a opção 3 no menu principal
2. Escolha o tipo de proxy (HTTP, SOCKS4, SOCKS5)
3. Digite o endereço no formato `ip:porta` ou `usuario:senha@ip:porta`

## ⚠️ Aviso Legal

**Esta ferramenta foi criada apenas para fins educacionais e de teste ético.**

O uso desta ferramenta contra sistemas sem permissão explícita é ilegal. O autor não se responsabiliza por qualquer uso indevido ou danos causados.

## 👨‍💻 Autor

- **GitHub**: [sentinelzxofc](https://github.com/sentinelzxofc)
- **Instagram**: [@sentinelzxofc](https://instagram.com/sentinelzxofc)

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<p align="center">
  <b>Collected-DBs - A melhor ferramenta para captura de bancos de dados no Termux</b>
</p>
