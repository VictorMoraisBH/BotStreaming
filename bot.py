import logging
import os
import datetime
import time
import telegram
import asyncio
import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackContext, ConversationHandler, PicklePersistence, CallbackContext, CommandHandler, CallbackQueryHandler, ConversationHandler
from dateutil.relativedelta import relativedelta

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ESCOLHER_CLIENTE, ESCOLHER_ACAO, ESCOLHER_ASSINATURA, EDITAR_ASSINATURA, APAGAR_ASSINATURA = range(5)

ADMIN_CHAT_ID = "5759744104"  # Substitua pelo seu ID real
TOKEN = "7745116159:AAGwXir_Asi5KqfU5GaEAUc7Vf4uQHtZc3E" # Substitua pelo token do seu bot

VALORES_PIX = {
    '1': 15.50, '2': 13.50, '3': 19.00
}

CHAVES_PIX = {
    frozenset(['1']): "00020101021126690014br.gov.bcb.pix01365ab5686d-99aa-49a3-a7b3-51a2e2e11aed0207Disney+520400005303986540515.505802BR5920VICTOR MORAIS CAMPOS6013BELO HORIZONT62070503***6304A0FE",
    frozenset(['2']): "00020101021126690014br.gov.bcb.pix01365ab5686d-99aa-49a3-a7b3-51a2e2e11aed0207YouTube520400005303986540513.505802BR5920VICTOR MORAIS CAMPOS6013BELO HORIZONT62070503***63043179",
    frozenset(['3']): "00020101021126650014br.gov.bcb.pix01365ab5686d-99aa-49a3-a7b3-51a2e2e11aed0203HBO520400005303986540519.005802BR5920VICTOR MORAIS CAMPOS6013BELO HORIZONT62070503***6304405E",
    frozenset(['1', '2']): "00020101021126750014br.gov.bcb.pix01365ab5686d-99aa-49a3-a7b3-51a2e2e11aed0213DisneyYoutube520400005303986540529.005802BR5920VICTOR MORAIS CAMPOS6013BELO HORIZONT62070503***63048D89",
    frozenset(['1', '3']): "00020101021126710014br.gov.bcb.pix01365ab5686d-99aa-49a3-a7b3-51a2e2e11aed0209DisneyHBO520400005303986540534.505802BR5920VICTOR MORAIS CAMPOS6013BELO HORIZONT62070503***6304EA3C",
    frozenset(['2', '3']): "00020101021126720014br.gov.bcb.pix01365ab5686d-99aa-49a3-a7b3-51a2e2e11aed0210YouTubeHBO520400005303986540532.505802BR5920VICTOR MORAIS CAMPOS6013BELO HORIZONT62070503***6304A016",
    frozenset(['1', '2', '3']): "00020101021126670014br.gov.bcb.pix01365ab5686d-99aa-49a3-a7b3-51a2e2e11aed0205Todos520400005303986540548.005802BR5920VICTOR MORAIS CAMPOS6013BELO HORIZONT62070503***6304444E",
}

PRODUTOS = {
    '1': "Disney+",
    '2': "YouTube Premium",
    '3': "HBO Max"
}

def salvar_historico(historico_compras):
    with open("historico_compras.json", "w", encoding="utf-8") as f:
        json.dump(historico_compras, f, indent=4, ensure_ascii=False)

def obter_chave_pix(carrinho_usuario):
    return CHAVES_PIX.get(frozenset(carrinho_usuario), None)

async def start(update: Update, context: CallbackContext):
    keyboard = [
        ["Novo por aqui", "Já sou cliente"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Bem-vindo! Você é novo por aqui ou já é cliente?", reply_markup=reply_markup)
    return "inicio"  # Retorna o estado "inicio"

async def inicio(update: Update, context: CallbackContext):
    resposta = update.message.text
    user_id = str(update.message.from_user.id)
    if resposta == "Novo por aqui":
        await update.message.reply_text(
            "Escolha os streams que deseja assinar (digite os números):\n"
            "1 - Disney+\n"
            "2 - YouTube Premium\n"
            "3 - HBO Max\n"
            "Digite os números separados por vírgula. Exemplo: 1, 2.\n\n"
            "Para finalizar a compra a qualquer momento, digite '0'."
        )
        return "escolher_servicos"  # Estado para escolher os serviços
    elif resposta == "Já sou cliente":
        keyboard = [
            ["Assinar mais um streaming", "Minha conta"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("O que você deseja fazer?", reply_markup=reply_markup)
        return "menu_cliente"  # Estado para o menu do cliente
    else:
        await update.message.reply_text("Resposta inválida. Escolha uma das opções.")
        return "inicio"

async def menu_cliente(update: Update, context: CallbackContext):
    resposta = update.message.text
    user_id = str(update.message.from_user.id)
    historico_compras = context.bot_data.get('historico_compras', {})

    if resposta == "Minha conta":
        if user_id in historico_compras:
            cliente_info = historico_compras[user_id]
            if "assinaturas" in cliente_info and cliente_info["assinaturas"]:
                assinaturas = cliente_info["assinaturas"]
                mensagem = "Seus streamings ativos:\n\n"

                for assinatura in assinaturas:
                    data_vencimento = assinatura.get('data_vencimento', 'Não Informado')
                    data_assinatura = assinatura.get('data_assinatura', 'Não Informada')

                    # Formatação para exibição (apenas aqui)
                    if data_vencimento != 'Não Informado':
                        try:
                            data_vencimento = datetime.datetime.strptime(data_vencimento, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except ValueError as e:
                            logging.error(f"Erro ao formatar data de vencimento: {e}")
                            data_vencimento = "Data Inválida"

                    if data_assinatura != 'Não Informada':
                        try:
                            data_assinatura = datetime.datetime.strptime(data_assinatura, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except ValueError as e:
                            logging.error(f"Erro ao formatar data de assinatura: {e}")
                            data_assinatura = "Data Inválida"

                    mensagem += f"● {assinatura['produto']}\n"
                    mensagem += f"- Dados de Acesso: E-mail: {assinatura.get('email', 'Não disponível')} / Senha: {assinatura.get('senha', 'Não disponível')},\n"
                    mensagem += f"- Vencimento: {data_vencimento}\n"
                    mensagem += f"- Assinatura: {data_assinatura},\n"
                    mensagem += f"✅Valor: R$ {assinatura.get('valor', 0.00):.2f}\n"
                    mensagem += "-------------------------------\n"

                mensagem += "\nPara suporte, envie um email para seu_email@exemplo.com"
                await update.message.reply_text(mensagem)
            else:
                await update.message.reply_text("Você ainda não possui nenhum stream ativo.\nPara suporte, envie um email para seu_email@exemplo.com")
        else:
            await update.message.reply_text("Você ainda não possui nenhum stream ativo.\nPara suporte, envie um email para seu_email@exemplo.com")
        return ConversationHandler.END
    elif resposta == "Assinar mais um streaming":
        await update.message.reply_text(
            "Escolha os streams que deseja assinar (digite os números):\n"
            "1 - Disney+\n"
            "2 - YouTube Premium\n"
            "3 - HBO Max\n"
            "Digite os números separados por vírgula. Exemplo: 1, 2.\n\n"
            "Para finalizar a compra a qualquer momento, digite 'finalizar'."
        )
        return "escolher_servicos"
    else:
        await update.message.reply_text("Opção inválida. Escolha uma das opções.")
        return "menu_cliente"

async def escolher_streaming(update: Update, context: CallbackContext):
    mensagem = update.message.text.strip().lower()
    user_id = str(update.message.from_user.id)
    historico_compras = context.bot_data.get('historico_compras', {})

    if mensagem == "0":  # Compara com "0"
        if user_id in historico_compras and "contato" in historico_compras[user_id]:
            await processar_compra(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text("Por favor, forneça seu contato (email ou telefone).")
            return "contato"

    if "carrinho" not in context.user_data:
        context.user_data["carrinho"] = []

    carrinho_usuario = context.user_data["carrinho"]

    try:
        escolhas = [e.strip() for e in mensagem.split(",")]
        for escolha in escolhas:
            if escolha.isdigit():
                if escolha in VALORES_PIX:
                    if escolha not in carrinho_usuario:
                        carrinho_usuario.append(escolha)
                        await update.message.reply_text(f"Serviço {PRODUTOS[escolha]} adicionado ao carrinho. Digite '0' para finalizar.") #Mensagem atualizada
                    else:
                        await update.message.reply_text(f"Você já adicionou o serviço {PRODUTOS[escolha]} ao carrinho.")
                else:
                    await update.message.reply_text(f"Opção inválida: {escolha}. Escolha entre 1, 2 e 3.")
            else:
                await update.message.reply_text(f"Entrada inválida: {escolha} não é um número.")
    except ValueError:
        await update.message.reply_text("Entrada inválida. Digite os números separados por vírgula.")
        return "escolher_servicos"

    context.user_data["carrinho"] = carrinho_usuario
    return "escolher_servicos"

async def processar_compra(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    nome_sobrenome = f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip()
    username = update.message.from_user.username or "Usuário sem username"

    try:
        historico_compras = context.bot_data.get('historico_compras', {})

        if "historico_compras_lock" not in context.bot_data:
            context.bot_data["historico_compras_lock"] = asyncio.Lock()

        async with context.bot_data["historico_compras_lock"]:
            if user_id in historico_compras and "contato" in historico_compras[user_id]:
                contato = historico_compras[user_id]["contato"]
                await update.message.reply_text(f"Utilizando o contato salvo: {contato}")
            else:
                contato = update.message.text
                historico_compras.setdefault(user_id, {})["contato"] = contato
                context.bot_data['historico_compras'] = historico_compras
                await update.message.reply_text(f"Contato salvo: {contato}")

        carrinho_usuario = context.user_data.get("carrinho", [])
        hoje = datetime.date.today()
        produtos_comprados = [PRODUTOS.get(item) for item in carrinho_usuario]
        produtos_comprados = [produto for produto in produtos_comprados if produto is not None]
        valor_total = sum([VALORES_PIX[item] for item in carrinho_usuario])
        data_vencimento = hoje + datetime.timedelta(days=30)
        chave_pix = obter_chave_pix(carrinho_usuario)
        itens = "\n".join([f"{PRODUTOS[item]} - R$ {VALORES_PIX[item]:.2f}" for item in carrinho_usuario])

        if chave_pix is None:
            await update.message.reply_text("Não foi possível gerar a chave Pix para o seu carrinho. Verifique os itens selecionados ou tente novamente mais tarde.")
            return ConversationHandler.END

        await update.message.reply_text(
            f"Carrinho de {nome_sobrenome}:\n{itens}\n\nTotal: R$ {valor_total:.2f}\n\nChave Pix: {chave_pix}\n\nApós realizar o pagamento, envie o comprovante."
        )

        compra_id = f"{user_id}_{time.time()}"

        compras_pendentes = context.bot_data.setdefault("compras_pendentes", {})
        compras_pendentes[compra_id] = {
            "user_id": user_id,
            "contato": contato,
            "produtos": produtos_comprados,
            "valor": valor_total,
            "data_compra": str(hoje),
            "data_vencimento": str(data_vencimento),
            "compra_id": compra_id
        }
        context.bot_data["compras_pendentes"] = compras_pendentes

        context.user_data.pop("carrinho", None)

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Novo pagamento iniciado por {nome_sobrenome} (@{username}) (ID: {user_id})\n"
            f"Contato: {contato}\n"
            f"Produtos Escolhidos: {', '.join(produtos_comprados)}\nTotal: R$ {valor_total:.2f}\nCompra ID: {compra_id}"
        )

        await context.application.persistence.flush()
        return "receber_comprovante"

    except (KeyError, TypeError, ValueError) as e:
        logging.error(f"Erro ao processar a compra: {e}")
        await update.message.reply_text("Ocorreu um erro ao processar sua compra. Tente novamente mais tarde.")
        return ConversationHandler.END
    except Exception as e:
        logging.exception(f"Erro inesperado ao processar a compra: {e}")
        await update.message.reply_text("Ocorreu um erro inesperado. Contate o suporte.")
        return ConversationHandler.END

async def receber_comprovante(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    nome_sobrenome = f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip()
    username = update.message.from_user.username or "Usuário sem username"
    historico_compras = context.bot_data.get('historico_compras', {})
    compras_pendentes = context.bot_data.get('compras_pendentes', {})

    compra_id_list = [compra_id for compra_id, compra_info in compras_pendentes.items() if compra_info.get("user_id") == user_id]

    if not compra_id_list:
        await update.message.reply_text("Você precisa ter um pedido pendente antes de enviar um comprovante.")
        return ConversationHandler.END

    compra_id = compra_id_list[0]
    compra = compras_pendentes.pop(compra_id) #Remove a compra da pendente

    try:
        if update.message.document:
            file = await update.message.document.get_file()
            file_path = os.path.join("comprovantes", f"{compra_id}.pdf")
            await file.download_to_drive(file_path)
        elif update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            file_path = os.path.join("comprovantes", f"{compra_id}.jpg")
            await photo_file.download_to_drive(file_path)
        else:
            await update.message.reply_text("Por favor, envie um comprovante de pagamento (foto ou documento).")
            return "receber_comprovante"

        # ***MOVENDO A LÓGICA DE CRIAÇÃO DA ASSINATURA PARA AQUI***
        data_assinatura = datetime.datetime.strptime(compra["data_compra"], '%Y-%m-%d').date()
        data_vencimento = datetime.datetime.strptime(compra["data_vencimento"], '%Y-%m-%d').date()

        for produto in compra["produtos"]:
            if user_id not in historico_compras:
                historico_compras[user_id] = {"assinaturas": []}
            elif "assinaturas" not in historico_compras[user_id]:
                historico_compras[user_id]["assinaturas"] = []

            assinatura_existente = next((a for a in historico_compras[user_id]["assinaturas"] if a["produto"] == produto), None)
            if assinatura_existente:
                assinatura_existente["data_vencimento"] = data_vencimento
                assinatura_existente["data_assinatura"] = data_assinatura
            else:
                historico_compras[user_id]["assinaturas"].append({
                    "produto": produto,
                    "data_vencimento": data_vencimento,
                    "data_assinatura": data_assinatura,
                    "dados_acesso": None,
                    "valor": compra["valor"]
                })
        context.bot_data['historico_compras'] = historico_compras
        context.bot_data["compras_pendentes"] = compras_pendentes
        await context.application.persistence.flush()

        await update.message.reply_text("Comprovante recebido e validado. Seus dados de acesso serão enviados em breve.")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Comprovante recebido de {nome_sobrenome} (@{username}) (ID: {user_id}). Compra ID: {compra_id}"
        )
        return ConversationHandler.END

    except telegram.error.TelegramError as te:
        logging.error(f"Erro do Telegram ao receber comprovante: {te}")
        await update.message.reply_text("Ocorreu um erro ao receber o comprovante. Tente novamente mais tarde.")
        return ConversationHandler.END
    except (OSError, IOError) as ioe:
        logging.error(f"Erro de arquivo ao salvar comprovante: {ioe}")
        await update.message.reply_text("Ocorreu um erro ao salvar o comprovante. Verifique as permissões da pasta.")
        return ConversationHandler.END
    except Exception as e:
        logging.exception(f"Erro inesperado ao receber comprovante: {e}")
        await update.message.reply_text("Ocorreu um erro inesperado. Contate o suporte.")
        return ConversationHandler.END

async def confirmar_pagamento(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("Você não tem permissão para executar este comando.")
        return

    if not context.args:
        await update.message.reply_text("Use: /confirmar_pagamento <ID_da_compra>")
        return

    compra_id = context.args[0]

    try:
        compras_pendentes = context.bot_data.get("compras_pendentes", {})
        if compra_id in compras_pendentes:
            compra_info = compras_pendentes[compra_id]
            user_id = str(compra_info["user_id"])

            historico_compras = context.bot_data.get('historico_compras', {})

            if user_id not in historico_compras: #Verifica se o user_id existe
                historico_compras[user_id] = {"assinaturas": []} #Cria o dicionario e a lista assinaturas
            elif "assinaturas" not in historico_compras[user_id]: #Verifica se o assinaturas existe
                historico_compras[user_id]["assinaturas"] = [] #Cria a lista assinaturas

            historico_compras[user_id]["assinaturas"].extend([
                {
                    "produto": produto,
                    "data_assinatura": compra_info["data_compra"],
                    "data_vencimento": compra_info["data_vencimento"],
                    "valor": compra_info["valor"]
                } for produto in compra_info["produtos"]
            ])

            context.bot_data['historico_compras'] = historico_compras
            del context.bot_data["compras_pendentes"][compra_id]
            context.application.persistence.flush()

            try:
                user = await context.bot.get_chat(int(user_id))
                nome_usuario = user.first_name + (f" {user.last_name}" if user.last_name else "")
                await context.bot.send_message(chat_id=int(user_id), text=f"Seu pagamento foi confirmado, {nome_usuario}! Agradecemos a compra. Seu pedido será processado em breve.")
                await update.message.reply_text(f"Pagamento da compra {compra_id} do usuario {nome_usuario} confirmado.")
            except telegram.error.BadRequest:
                await update.message.reply_text(f"Pagamento da compra {compra_id} confirmado. Não foi possivel enviar a mensagem para o usuario.")
            except telegram.error.TelegramError as e:
                logger.error(f"Erro ao enviar mensagem de confirmação: {e}")
                await update.message.reply_text(f"Pagamento da compra {compra_id} confirmado. Ocorreu um erro ao enviar a confirmação para o usuário.")

        else:
            await update.message.reply_text(f"Nenhuma compra pendente encontrada com o ID: {compra_id}.")

    except ValueError:
        await update.message.reply_text("ID da compra inválido.")
    except Exception as e:
        logger.exception(f"Erro ao confirmar pagamento: {e}")
        logger.error(f"Dados relevantes: historico_compras: {json.dumps(context.bot_data.get('historico_compras'), indent=4, default=str)}, compras_pendentes: {json.dumps(context.bot_data.get('compras_pendentes'), indent=4, default=str)}") #Loga os dados
        await update.message.reply_text(f"Ocorreu um erro ao confirmar o pagamento: {e}")

async def cancelar(update: Update, context: CallbackContext):
    await update.message.reply_text("Operação cancelada.")  # Linha corrigida: INDENTADA
    return ConversationHandler.END

async def enviar_acesso(update: telegram.Update, context: telegram.ext.CallbackContext):
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("Você não tem permissão para executar este comando.")
        return

    if len(context.args) < 4:
        await update.message.reply_text("Use: /enviar_acesso <ID_do_usuário> <Assinatura> E-mail: <email> Senha: <senha>")
        return

    try:
        user_id = int(context.args[0])
        logging.info(f"context.args completo: {context.args}")

        try:
            email_index = context.args.index("E-mail:")
        except ValueError:
            await update.message.reply_text("Formato incorreto. Certifique-se de usar 'E-mail:' e 'Senha:'")
            return

        assinatura_args = context.args[1:email_index]
        assinatura_com_aspas = " ".join(assinatura_args)
        assinatura = assinatura_com_aspas.replace('"', '').strip()

        try:
            dados_acesso = " ".join(context.args[email_index:])
            dados_acesso_parts = dados_acesso.split("Senha:")
            email = dados_acesso_parts[0].replace("E-mail:", "").strip()
            senha = dados_acesso_parts[1].strip()

            if not email or not senha:
                raise ValueError("E-mail ou senha não informados corretamente.")

        except (IndexError, ValueError) as e:
            await update.message.reply_text(f"Formato incorreto dos dados de acesso. Use: E-mail: <email> Senha: <senha>. Erro: {e}")
            logging.error(f"Formato incorreto dos dados de acesso: {e}")
            return

        logging.info(f"Enviando acesso para usuário {user_id}, assinatura: {assinatura}, email: {email}, senha: {senha}")
        logging.info(f"historico_compras COMPLETO: {context.bot_data}")

        # ***CORREÇÃO PRINCIPAL: Cria a estrutura se não existir***
        if 'historico_compras' not in context.bot_data:
            context.bot_data['historico_compras'] = {}
            await context.application.persistence.flush() #Salva as mudanças no arquivo pickle

        historico_compras = context.bot_data['historico_compras'] #Acessa o historico_compras sem o get

        user_id_str = str(user_id)

        if user_id_str not in historico_compras:
            historico_compras[user_id_str] = {"assinaturas": []}
            context.bot_data['historico_compras'] = historico_compras #Atualiza o historico_compras
            await context.application.persistence.flush() #Salva as mudanças no arquivo pickle
            await update.message.reply_text(f"Nenhuma assinatura encontrada para o usuário {user_id}. Uma nova entrada foi criada.")
            logging.warning(f"Nenhuma assinatura encontrada para o usuario {user_id} no historico de compras. Uma nova entrada foi criada.")
            

        if "assinaturas" not in historico_compras[user_id_str]:
            historico_compras[user_id_str]["assinaturas"] = []
            context.bot_data['historico_compras'] = historico_compras #Atualiza o historico_compras
            await context.application.persistence.flush() #Salva as mudanças no arquivo pickle
            await update.message.reply_text(f"Nenhuma assinatura encontrada para o usuário {user_id}. Uma nova entrada foi criada.")
            logging.warning(f"Nenhuma assinatura encontrada para o usuario {user_id} no historico de compras. Uma nova entrada foi criada.")

        assinatura_encontrada = next((a for a in historico_compras[user_id_str]["assinaturas"] if a["produto"] == assinatura), None)

        if assinatura_encontrada is None:
            await update.message.reply_text(f"A assinatura '{assinatura}' não foi encontrada para o usuário {user_id}.")
            logging.warning(f"Assinatura '{assinatura}' não encontrada para o usuário {user_id} nas assinaturas existentes: {historico_compras[user_id_str].get('assinaturas')}")
            return

        try:
            await context.bot.send_message(chat_id=user_id, text=f"Seus dados de acesso para {assinatura}:\nE-mail: {email}\nSenha: {senha}")
            await update.message.reply_text(f"Dados de acesso para {assinatura} enviados para o usuário {user_id}.")

            index_assinatura = historico_compras[user_id_str]["assinaturas"].index(assinatura_encontrada)
            historico_compras[user_id_str]["assinaturas"][index_assinatura]["email"] = email
            historico_compras[user_id_str]["assinaturas"][index_assinatura]["senha"] = senha

            context.bot_data['historico_compras'] = historico_compras
            await context.application.persistence.flush()
            logging.info(f"Dados de acesso enviados com sucesso para o usuario {user_id}, assinatura: {assinatura}")

        except telegram.error.BadRequest:
            await update.message.reply_text(f"Usuário com ID {user_id} não encontrado ou bloqueou o bot.")
            logging.error(f"Erro ao enviar mensagem para o usuario {user_id}: Usuario nao encontrado ou bloqueou o bot.")
        except telegram.error.TelegramError as e:
            logging.error(f"Erro ao enviar mensagem de acesso para usuario {user_id}: {e}")
            await update.message.reply_text(f"Ocorreu um erro ao enviar os dados de acesso: {e}")

    except ValueError:
        await update.message.reply_text("ID do usuário inválido. Use um número inteiro.")
        logging.error(f"ID do usuario invalido.")
    except Exception as e:
        logging.exception(f"Erro inesperado ao executar /enviar_acesso: {e}")
        await update.message.reply_text("Ocorreu um erro inesperado. Contate o suporte.")

async def exibir_info_cliente(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("Você não tem permissão para executar este comando.")
        return

    if not context.args:
        await update.message.reply_text("Use: /cliente <ID_do_cliente>")
        return

    user_id_str = str(context.args[0])  # Mantém o ID como string para busca no dicionário
    historico_compras = context.bot_data.get('historico_compras', {})

    if user_id_str in historico_compras:
        cliente_info = historico_compras[user_id_str]
        contato = cliente_info.get("contato", "Não Informado")

        try:
            user = await context.bot.get_chat(int(user_id_str))
            nome_usuario = user.first_name + (f" {user.last_name}" if user.last_name else "")
        except telegram.error.BadRequest:
            nome_usuario = "Nome não encontrado (usuário pode ter bloqueado o bot)"
        except telegram.error.TelegramError as e:
            logging.error(f"Erro ao obter informações do usuário: {e}")
            nome_usuario = "Erro ao obter nome do usuário"

        mensagem = f"Informações do cliente: {nome_usuario} (ID: {user_id_str})\n"
        mensagem += f"Contato: {contato}\n"
        mensagem += "Assinaturas:\n"

        if "assinaturas" in cliente_info and cliente_info["assinaturas"]:
            for assinatura in cliente_info["assinaturas"]:
                produto = assinatura.get('produto', 'Não Informado')
                email = assinatura.get('email', 'Não Informado')
                senha = assinatura.get('senha', 'Não Informada')
                data_vencimento = assinatura.get('data_vencimento', 'Não Informado')
                data_assinatura = assinatura.get('data_assinatura', 'Não Informada')
                valor = assinatura.get('valor', 0.00)

                dados_acesso = f"E-mail: {email}, Senha: {senha}" if email != 'Não Informado' and senha != 'Não Informada' else 'Não Informados'

                mensagem += f"- {produto} (Dados de Acesso: {dados_acesso}, Vencimento: {data_vencimento}, Assinatura: {data_assinatura}, Valor: R$ {valor:.2f})\n"
        else:
            mensagem += "Nenhuma assinatura ativa.\n"  # Mensagem mais clara

        await update.message.reply_text(mensagem)
    else:
        await update.message.reply_text(f"Nenhum cliente encontrado com o ID: {user_id_str}")

async def enviar_lembrete_cobranca(context: CallbackContext):
    """Envia lembretes de cobrança."""
    historico_compras = context.bot_data.get('historico_compras', {})
    hoje = datetime.date.today()

    for user_id, dados_usuario in historico_compras.items():
        for assinatura in dados_usuario.get("assinaturas", []):
            try:
                data_vencimento = datetime.datetime.strptime(assinatura["data_vencimento"], "%Y-%m-%d").date()
                dias_restantes = (data_vencimento - hoje).days
                valor = assinatura["valor"]
                produto = assinatura["produto"]

                if dias_restantes == 2:
                    await context.bot.send_message(chat_id=user_id, text=f"Lembrete: Sua assinatura do {produto} vence em 2 dias (dia {data_vencimento.strftime('%d/%m/%Y')}). Valor: R$ {valor:.2f}")
                elif dias_restantes == 0:
                    try:
                        produto_numero = [key for key, value in PRODUTOS.items() if value == produto][0]
                        chave_pix = obter_chave_pix([produto_numero])
                        if chave_pix:
                            await context.bot.send_message(chat_id=user_id, text=f"Sua assinatura do {produto} vence hoje! Utilize a chave Pix abaixo para renovar: \n{chave_pix}\nValor: R$ {valor:.2f}")
                        else:
                            await context.bot.send_message(chat_id=user_id, text=f"Sua assinatura do {produto} venceu hoje, estamos com problemas para gerar a chave pix, entre em contato para mais informações")
                    except Exception as e:
                        logging.error(f"Erro ao obter chave pix: {e}")
                        await context.bot.send_message(chat_id=user_id, text=f"Erro ao gerar chave pix para {produto}, entre em contato com o suporte")
                elif dias_restantes < 0:
                    await context.bot.send_message(chat_id=user_id, text=f"Sua assinatura do {produto} venceu dia {data_vencimento.strftime('%d/%m/%Y')}, entre em contato para regularizar a sua situação")

            except ValueError as e:
                logging.error(f"Erro ao processar data para o usuário {user_id}: Data inválida no historico_compras: {e}")
                continue
            except Exception as e:
                logging.error(f"Erro desconhecido ao enviar lembrete de cobrança: {e}")
                continue

            await context.application.persistence.flush() #Adiciona o await aqui

async def finalizar_compra(update: Update, context: CallbackContext):
    if "carrinho" not in context.user_data or not context.user_data["carrinho"]:
        await update.message.reply_text("Seu carrinho está vazio. Adicione itens para continuar.")
        return ConversationHandler.END

    await update.message.reply_text("Por favor, forneça seu contato (email ou telefone).")
    return "contato" 

async def listar_compras_pendentes(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("Você não tem permissão para executar este comando.")
        return

    compras_pendentes = context.bot_data.get("compras_pendentes", {})
    if compras_pendentes:
        mensagem = "Compras Pendentes:\n"
        for compra_id, compra_info in compras_pendentes.items():
            mensagem += f"ID: {compra_id}, Usuário: {compra_info['user_id']}, Produtos: {', '.join(compra_info['produtos'])}, Valor: R$ {compra_info['valor']:.2f}\n"
        await update.message.reply_text(mensagem)
    else:
        await update.message.reply_text("Nenhuma compra pendente.")

async def listar_clientes_ativos(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("Você não tem permissão para executar este comando.")
        return

    historico_compras = context.bot_data.get('historico_compras', {})
    mensagem = "Clientes Ativos:\n"

    for user_id, cliente_info in historico_compras.items():
        if "assinaturas" in cliente_info and cliente_info["assinaturas"]:
            try:
                user = await context.bot.get_chat(int(user_id))
                nome_usuario = user.first_name + (f" {user.last_name}" if user.last_name else "")
            except telegram.error.BadRequest:
                nome_usuario = "Nome não encontrado (usuário pode ter bloqueado o bot)"
            except telegram.error.TelegramError as e:
                logging.error(f"Erro ao obter informações do usuário {user_id}: {e}")
                nome_usuario = f"Erro ao obter nome do usuário {user_id}"
            mensagem += f"\n- {nome_usuario} (ID: {user_id}):\n"
            for assinatura in cliente_info["assinaturas"]:
                data_assinatura = assinatura.get('data_assinatura')
                data_vencimento = assinatura.get('data_vencimento')

                assinatura_str = "Não Informada"
                vencimento_str = "Não Informado"

                if data_assinatura:
                    if isinstance(data_assinatura, str):
                        try:
                            data_assinatura = datetime.datetime.strptime(data_assinatura, '%Y-%m-%d').date()
                        except ValueError as e:
                            logging.error(f"Erro ao converter data de assinatura (usuário {user_id}, produto {assinatura.get('produto')}): {e}, valor original: {assinatura.get('data_assinatura')}")
                            assinatura_str = "Data Inválida"
                        else:
                            assinatura_str = data_assinatura.strftime('%d/%m/%Y')
                    elif isinstance(data_assinatura, datetime.date):
                        assinatura_str = data_assinatura.strftime('%d/%m/%Y')
                    else:
                        logging.error(f"Tipo incorreto de data_assinatura (usuário {user_id}, produto {assinatura.get('produto')}): {type(data_assinatura)}, Valor: {data_assinatura}")
                        assinatura_str = "Erro na Data"

                if data_vencimento:
                    if isinstance(data_vencimento, str):
                        try:
                            data_vencimento = datetime.datetime.strptime(data_vencimento, '%Y-%m-%d').date()
                        except ValueError as e:
                            logging.error(f"Erro ao converter data de vencimento (usuário {user_id}, produto {assinatura.get('produto')}): {e}, valor original: {assinatura.get('data_vencimento')}")
                            vencimento_str = "Data Inválida"
                        else:
                            vencimento_str = data_vencimento.strftime('%d/%m/%Y')
                    elif isinstance(data_vencimento, datetime.date):
                        vencimento_str = data_vencimento.strftime('%d/%m/%Y')
                    else:
                        logging.error(f"Tipo incorreto de data_vencimento (usuário {user_id}, produto {assinatura.get('produto')}): {type(data_vencimento)}, Valor: {data_vencimento}")
                        vencimento_str = "Erro na Data"

                mensagem += f" - {assinatura.get('produto', 'Produto não informado')} (Dados de Acesso: {assinatura.get('dados_acesso', 'Não Informados')}, Vencimento: {vencimento_str}, Assinatura: {assinatura_str}, Valor: R$ {assinatura.get('valor', 0.00):.2f})\n"

    await update.message.reply_text(mensagem)

async def apagar_cliente(update: Update, context: CallbackContext):
    user_id_admin = str(update.message.from_user.id)

    if user_id_admin != str(ADMIN_CHAT_ID):
        await update.message.reply_text("Você não tem permissão para usar este comando.")
        return

    try:
        args = context.args  # Obtém os argumentos do comando
        if not args:
            await update.message.reply_text("Por favor, especifique o ID do cliente a ser apagado. Ex: /apagar_cliente 123456789")
            return

        cliente_id_para_apagar = str(args[0])

        historico_compras = context.bot_data.get('historico_compras', {})

        if cliente_id_para_apagar in historico_compras:
            async with context.bot_data.get("historico_compras_lock"): #Acessa o historico com o lock
                del historico_compras[cliente_id_para_apagar]
                context.bot_data['historico_compras'] = historico_compras #Atualiza o bot_data
            await context.application.persistence.flush()
            await update.message.reply_text(f"Cliente com ID {cliente_id_para_apagar} apagado do histórico.")
        else:
            await update.message.reply_text(f"Cliente com ID {cliente_id_para_apagar} não encontrado no histórico.")

    except ValueError:
        await update.message.reply_text("ID do cliente inválido. Use apenas números.")
    except Exception as e:
        logger.exception(f"Erro ao apagar cliente: {e}")
        await update.message.reply_text("Ocorreu um erro ao apagar o cliente.")

async def gerenciar_assinaturas(update: Update, context: CallbackContext):
    logging.info("gerenciar_assinaturas: INÍCIO")
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id_admin = str(query.from_user.id)
    elif update.message:
        user_id_admin = str(update.message.from_user.id)
    else:
        logging.error("Update recebido não é nem callback query nem mensagem.")
        return ConversationHandler.END

    logging.info(f"ADMIN_CHAT_ID: {ADMIN_CHAT_ID}, user_id_admin: {user_id_admin}") #Log para verificar os ids
    if user_id_admin != str(ADMIN_CHAT_ID):
        mensagem = "Você não tem permissão para usar este comando."
        if update.callback_query:
            await update.callback_query.edit_message_text(mensagem)
        else:
            await update.message.reply_text(mensagem)
        return ConversationHandler.END

    historico_compras = context.bot_data.get('historico_compras', {})
    logging.info(f"historico_compras: {historico_compras}") #Log para verificar o historico_compras

    if not historico_compras:
        mensagem = "Nenhum cliente com assinaturas encontrado."
        if update.callback_query:
            await update.callback_query.edit_message_text(mensagem)
        else:
            await update.message.reply_text(mensagem)
        return ConversationHandler.END

    keyboard = []
    for cliente_id, info_cliente in historico_compras.items():
        if "assinaturas" in info_cliente and info_cliente["assinaturas"]:
            try:
                user = await context.bot.get_chat(int(cliente_id))
                nome_cliente = f"{user.first_name} {user.last_name or ''}".strip()
            except telegram.error.TelegramError as e:
                logging.error(f"Erro ao obter informações do usuário {cliente_id}: {e}")
                nome_cliente = f"Cliente ID: {cliente_id} (Informações não disponíveis)"
            keyboard.append([InlineKeyboardButton(nome_cliente, callback_data=f"cliente_{cliente_id}")])

    if not keyboard:
        mensagem = "Nenhum cliente com assinaturas encontrado."
        if update.callback_query:
            await update.callback_query.edit_message_text(mensagem)
        else:
            await update.message.reply_text(mensagem)
        return ConversationHandler.END

    reply_markup = InlineKeyboardMarkup(keyboard)
    mensagem = "Selecione o cliente para gerenciar as assinaturas:"
    if update.callback_query:
        await update.callback_query.edit_message_text(mensagem, reply_markup=reply_markup)
    else:
        await update.message.reply_text(mensagem, reply_markup=reply_markup)
    logging.info("gerenciar_assinaturas: FIM - Retornando ESCOLHER_CLIENTE")
    return ESCOLHER_CLIENTE

async def escolher_acao(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    cliente_id = query.data.split("_")[1]
    context.user_data["cliente_id"] = cliente_id
    logging.info(f"escolher_acao: INÍCIO - cliente_id = {cliente_id}")

    editar_callback_data = f"editar_{cliente_id}"
    apagar_callback_data = f"apagar_{cliente_id}"
    voltar_callback_data = "voltar_clientes"

    logging.info(f"escolher_acao: editar_callback_data = {editar_callback_data}")
    logging.info(f"escolher_acao: apagar_callback_data = {apagar_callback_data}")
    logging.info(f"escolher_acao: voltar_callback_data = {voltar_callback_data}")

    keyboard = [
        [InlineKeyboardButton("Editar Assinatura", callback_data=editar_callback_data),
        InlineKeyboardButton("Apagar Assinatura", callback_data=apagar_callback_data)],
        [InlineKeyboardButton("Voltar para Clientes", callback_data=voltar_callback_data)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Selecione a ação:", reply_markup=reply_markup)
    logging.info("escolher_acao: FIM - Retornando ESCOLHER_ACAO")
    return ESCOLHER_ACAO

async def escolher_assinatura(update: Update, context: CallbackContext):
    logging.info("escolher_assinatura: INÍCIO")
    query = update.callback_query
    await query.answer()

    if query.data == "voltar_clientes":
        context.user_data.pop('cliente_id', None)
        return await gerenciar_assinaturas(update, context)

    cliente_id = context.user_data.get('cliente_id')
    logging.info(f"escolher_assinatura: cliente_id = {cliente_id}")
    if cliente_id is None:
        await query.edit_message_text(text="Cliente não selecionado. Inicie o gerenciamento novamente.")
        return ConversationHandler.END

    historico_compras = context.bot_data.get("historico_compras", {})
    cliente_info = historico_compras.get(str(cliente_id)) #Converte para string antes de acessar o dicionario

    if not cliente_info or "assinaturas" not in cliente_info or not cliente_info["assinaturas"]:
        await query.edit_message_text(text=f"Este cliente (ID: {cliente_id}) não possui assinaturas ou não foi encontrado.")
        return ESCOLHER_CLIENTE

    keyboard = []
    for i, assinatura in enumerate(cliente_info["assinaturas"]):
        produto = assinatura.get('produto', 'Não Informado')
        data_vencimento = assinatura.get('data_vencimento', 'Não Informado')
        callback_data = f"assinatura_{cliente_id}_{i}"
        keyboard.append([InlineKeyboardButton(f"{produto} (Vencimento: {data_vencimento})", callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("Voltar para Ações", callback_data=f"voltar_acoes_{cliente_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Selecione a assinatura:", reply_markup=reply_markup)
    logging.info("escolher_assinatura: FIM - Retornando ESCOLHER_ASSINATURA")
    return ESCOLHER_ASSINATURA

async def executar_acao(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    logging.info(f"executar_acao: query.data = {query.data}") # Log crucial

    if query.data == "voltar_clientes":
        logging.info("executar_acao: Retornando ESCOLHER_CLIENTE") # Log crucial
        return ESCOLHER_CLIENTE

    elif query.data.startswith("voltar_acoes_"):
        cliente_id = query.data.split("_")[2]
        context.user_data["cliente_id"] = cliente_id
        return ESCOLHER_ASSINATURA # Correto: Retorna o ESTADO
    
    elif query.data.startswith("voltar_assinaturas_"):
        cliente_id = context.user_data.get("cliente_id")
        return ESCOLHER_ACAO # Correto: Retorna o ESTADO

    elif query.data.startswith("editar_"):
        cliente_id = query.data.split("_")[1]
        context.user_data["cliente_id"] = cliente_id
        return EDITAR_ASSINATURA # Correto: Retorna o ESTADO

    elif query.data.startswith("apagar_"):
        cliente_id = query.data.split("_")[1]
        context.user_data["cliente_id"] = cliente_id
        return APAGAR_ASSINATURA # Correto: Retorna o ESTADO

    else:
        return ConversationHandler.END

async def editar_assinatura(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cliente_id = context.user_data.get("cliente_id")
    logging.info(f"editar_assinatura: INÍCIO - cliente_id: {cliente_id}")
    if cliente_id is None:
        await query.edit_message_text(text="Cliente não selecionado. Inicie o gerenciamento novamente.")
        return ConversationHandler.END

    # ***AQUI VAI A LÓGICA PARA EDITAR A ASSINATURA***
    await query.edit_message_text("Edite a assinatura aqui (em desenvolvimento).")

    keyboard = [[InlineKeyboardButton("Voltar para Assinaturas", callback_data=f"voltar_assinaturas_{cliente_id}")]] #Botão Voltar
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

    logging.info("editar_assinatura: FIM - Aguardando callback do botão Voltar")
    return EDITAR_ASSINATURA

async def apagar_assinatura(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cliente_id = context.user_data.get("cliente_id")
    logging.info(f"apagar_assinatura: INÍCIO - cliente_id: {cliente_id}")
    if cliente_id is None:
        await query.edit_message_text(text="Cliente não selecionado. Inicie o gerenciamento novamente.")
        return ConversationHandler.END

    # ***AQUI VAI A LÓGICA PARA APAGAR A ASSINATURA***
    await query.edit_message_text("Apague a assinatura aqui (em desenvolvimento).")

    keyboard = [[InlineKeyboardButton("Voltar para Assinaturas", callback_data=f"voltar_assinaturas_{cliente_id}")]] #Botão Voltar
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

    logging.info("apagar_assinatura: FIM - Aguardando callback do botão Voltar")
    return APAGAR_ASSINATURA

async def comando_gerenciar_assinaturas(update: Update, context: CallbackContext):
    await gerenciar_assinaturas(update, context)
    return ESCOLHER_CLIENTE

async def exibir_acoes_cliente(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    cliente_id = query.data.split("_")[1]
    context.user_data["cliente_id"] = cliente_id # Usando context.user_data correto.
    logging.info(f"exibir_acoes_cliente: cliente_id = {cliente_id}")

    keyboard = [
        [InlineKeyboardButton("Voltar", callback_data="voltar_clientes")], #Voltar para a lista de clientes
        [
            InlineKeyboardButton("Editar Assinatura", callback_data=f"editar_{cliente_id}"), #callback_data corrigido
            InlineKeyboardButton("Apagar Assinatura", callback_data=f"apagar_{cliente_id}"), #callback_data corrigido
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Ações para o cliente {cliente_id}:", reply_markup=reply_markup)
    return ESCOLHER_ACAO #Retorna para o estado correto.

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    persistence_file = os.path.join(script_dir, "bot_data.pickle")
    persistence = PicklePersistence(filepath=persistence_file)
    comprovantes_dir = os.path.join(script_dir, "comprovantes")
    os.makedirs(comprovantes_dir, exist_ok=True)

    application = Application.builder().token(TOKEN).persistence(persistence).build()

    if "historico_compras" not in application.bot_data:
        application.bot_data["historico_compras"] = {}
    if "compras_pendentes" not in application.bot_data:
        application.bot_data["compras_pendentes"] = {}
    if "historico_compras_lock" not in application.bot_data:
        application.bot_data["historico_compras_lock"] = asyncio.Lock()
    job_queue = application.job_queue

    async def executar_teste_agora(context: CallbackContext):
        await enviar_lembrete_cobranca(context)

    job_queue.run_once(executar_teste_agora, when=5.0)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            "inicio": [MessageHandler(filters.TEXT, inicio)],
            "menu_cliente": [MessageHandler(filters.TEXT, menu_cliente)],
            "escolher_servicos": [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_streaming)],
            "contato": [MessageHandler(filters.TEXT, processar_compra)],
            "receber_comprovante": [MessageHandler(filters.PHOTO | filters.Document.ALL, receber_comprovante)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        name="main_conversation",
        persistent=True,
        allow_reentry=True
    )

    conv_handler_gerenciar_assinaturas = ConversationHandler(
    entry_points=[CommandHandler('gerenciar_assinaturas', comando_gerenciar_assinaturas)],
    states={
        ESCOLHER_CLIENTE: [CallbackQueryHandler(escolher_acao, pattern="^cliente_")],
        ESCOLHER_ACAO: [
            CallbackQueryHandler(executar_acao, pattern=r"^editar_"),
            CallbackQueryHandler(executar_acao, pattern=r"^apagar_"),
            CallbackQueryHandler(executar_acao, pattern=r"^voltar_clientes$"),
            CallbackQueryHandler(escolher_assinatura, pattern=r"^voltar_acoes_"),
            CallbackQueryHandler(executar_acao, pattern=r"^voltar_assinaturas_")
        ],
        ESCOLHER_ASSINATURA: [
            CallbackQueryHandler(escolher_assinatura, pattern=r"^assinatura_"),
            CallbackQueryHandler(executar_acao, pattern=r"^voltar_acoes_"), #Voltar para as ações
            CallbackQueryHandler(executar_acao, pattern=r"^voltar_clientes$")
        ],
        EDITAR_ASSINATURA: [
            CallbackQueryHandler(executar_acao, pattern=r"^voltar_assinaturas_"),  # Handler para voltar
        ],
        APAGAR_ASSINATURA: [
            CallbackQueryHandler(executar_acao, pattern=r"^voltar_assinaturas_"),  # Handler para voltar
        ],
    },
    fallbacks=[CommandHandler("cancelar", cancelar)],
    name="gerenciar_assinaturas_conversation",
    allow_reentry=True
)

    #Removido o handler do clientes ativos
    apagar_cliente_handler = CommandHandler("apagar_cliente", apagar_cliente)

    application.add_handler(conv_handler)
    application.add_handler(conv_handler_gerenciar_assinaturas)
    application.add_handler(apagar_cliente_handler)
    application.add_handler(CommandHandler("confirmar_pagamento", confirmar_pagamento))
    application.add_handler(CommandHandler("enviar_acesso", enviar_acesso))
    application.add_handler(CommandHandler("cliente", exibir_info_cliente))

    application.run_polling()

if __name__ == "__main__":
    main() 