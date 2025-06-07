import json
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import time, datetime, date
import pytz
import random
import PyPDF2
import os

# Funzione per leggere il contenuto del PDF
def get_pdf_content():
    if os.path.exists('info.pdf'):
        try:
            with open('info.pdf', 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Errore nella lettura del PDF: {e}")
            return None
    return None


# Carica le variabili d'ambiente
# Aggiungi questa variabile dopo il caricamento delle variabili d'ambiente
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
AI_API = os.getenv('AI_API')

# Aggiungi questa funzione per configurare Gemini
def setup_gemini():
    if AI_API:
        genai.configure(api_key=AI_API)
        return True
    return False

# Funzione per caricare gli utenti dal file JSON
def load_users():
    try:
        with open('users.json', 'r') as file:
            content = file.read()
            if not content.strip():
                return {"users": []}
            file.seek(0)
            return json.load(file)
    except FileNotFoundError:
        return {"users": []}
    except json.JSONDecodeError:
        print("Attenzione: Il file 'users.json' è vuoto o contiene JSON non valido. Verrà trattato come nuovo.")
        return {"users": []}# Funzione per caricare le statistiche

def load_stats():
    try:
        with open('stats.json', 'r') as file:
            # Per gestire il caso di file completamente vuoto prima che json.load dia errore
            content = file.read()
            if not content.strip(): # Se il file è vuoto o contiene solo spazi bianchi
                return {}
            # Se c'è contenuto, torna all'inizio del file e carica
            file.seek(0)
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Attenzione: Il file 'stats.json' è vuoto o contiene JSON non valido. Verrà trattato come vuoto.")
        return {} # Tratta il file corrotto/vuoto come se fosse un nuovo file

# Funzione per salvare le statistiche
def save_stats(stats):
    with open('stats.json', 'w') as file:
        json.dump(stats, file, indent=4)

# Funzione per aggiornare le statistiche dell'utente
def update_user_stats(user_id, is_correct):
    stats = load_stats()
    today = str(date.today())

    if str(user_id) not in stats:
        stats[str(user_id)] = {}

    if today not in stats[str(user_id)]:
        stats[str(user_id)][today] = {"correct": 0, "wrong": 0}

    if is_correct:
        stats[str(user_id)][today]["correct"] += 1
    else:
        stats[str(user_id)][today]["wrong"] += 1

    save_stats(stats)

async def get_ai_explanation(question, correct_answer_key, answer_mapping): # correct_answer_key è tipo "Risposta1"
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17-thinking')

        shuffled_answers_display = [] # Lista di tuple (lettera, testo_risposta)
        # Ricostruisci l'ordine delle risposte come visualizzato dall'utente
        # answer_mapping mappa '0' (indice UI) -> '2' (indice originale della risposta)
        for ui_idx_str in sorted(answer_mapping.keys(), key=int): # '0', '1', '2', '3'
            original_idx_str = answer_mapping[ui_idx_str] # es. '2'
            letter = chr(65 + int(ui_idx_str)) # A, B, C, D
            answer_text = question[f'Risposta{original_idx_str}']
            shuffled_answers_display.append((letter, answer_text))

        additional_context = get_pdf_content()

        base_prompt = f"""
        Riguardo questa domanda di etica: "{question['Domanda']}"

        Le possibili risposte erano mostrate in questo ordine:
        """
        for letter, text in shuffled_answers_display:
            base_prompt += f"\n{letter}) {text}"

        # Trova la lettera della risposta corretta
        correct_letter_display = ""
        correct_answer_text = question[correct_answer_key] # Testo della risposta corretta
        for letter, text in shuffled_answers_display:
            if text == correct_answer_text:
                correct_letter_display = letter
                break
        
        base_prompt += f"\n\nLa risposta corretta è: {correct_letter_display}) {correct_answer_text}"

        if additional_context:
            prompt = f"""
            Utilizzando il seguente contesto aggiuntivo:

            {additional_context}

            {base_prompt}

            Puoi fornire una spiegazione chiara e concisa (max 150 parole) del perché questa è la risposta corretta,
            facendo riferimento alle informazioni del contesto dove pertinente?
            """
        else:
            prompt = base_prompt + "\n\nPuoi fornire una spiegazione chiara e concisa (max 150 parole) del perché questa è la risposta corretta?"

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Errore nell'ottenere la spiegazione AI: {e}")
        return None
# Funzione per inviare le statistiche giornaliere
async def send_daily_stats(context):
    stats = load_stats()
    users = load_users()
    today = str(date.today())

    for user in users['users']:
        user_id = str(user['id'])
        if user_id in stats and today in stats[user_id]:
            user_stats = stats[user_id][today]
            total_questions = user_stats["correct"] + user_stats["wrong"]
            correct_answers = user_stats["correct"]

            message = f"📊 Statistiche del giorno {today}:\n\n"
            message += f"Totale domande risposte: {total_questions}\n"
            message += f"Risposte corrette: {correct_answers}\n"
            message += f"Percentuale di successo: {(correct_answers/total_questions*100):.1f}%"

            try:
                await context.bot.send_message(
                    chat_id=user['id'],
                    text=message
                )
            except Exception as e:
                print(f"Errore nell'invio delle statistiche all'utente {user_id}: {e}")

# Funzione per salvare gli utenti nel file JSON
def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file, indent=4)

# Funzione per aggiungere un nuovo utente
def add_user(user):
    users = load_users()
    user_exists = any(u['id'] == user['id'] for u in users['users'])

    if not user_exists:
        user['reminders_enabled'] = True
        users['users'].append(user)
        save_users(users)
        return True
    return False

# Carica le domande dal file JSON
def load_questions():
    with open('updated_domande.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Funzione per ottenere una domanda casuale
def get_random_question():
    questions = load_questions()
    return random.choice(questions)

# Funzione per creare la tastiera con le risposte
def get_keyboard():
    keyboard = [
        [InlineKeyboardButton("A", callback_data='ans_0')],
        [InlineKeyboardButton("B", callback_data='ans_1')],
        [InlineKeyboardButton("C", callback_data='ans_2')],
        [InlineKeyboardButton("D", callback_data='ans_3')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_ai_explanation(question, correct_answer, answer_mapping):
    try:
        model = genai.GenerativeModel('gemini-pro')

        # Crea la lista delle risposte nell'ordine mostrato all'utente
        shuffled_answers = []
        for i in range(4):
            original_idx = answer_mapping[str(i)]
            shuffled_answers.append((chr(65+i), question[f'Risposta{original_idx}']))

        additional_context = get_pdf_content()

        # Costruisci il prompt con le risposte nell'ordine mostrato
        base_prompt = f"""
        Riguardo questa domanda di etica: "{question['Domanda']}"

        Le possibili risposte erano mostrate in questo ordine:
        """

        # Aggiungi le risposte nell'ordine in cui sono state mostrate
        for letter, answer in shuffled_answers:
            base_prompt += f"\n{letter}) {answer}"

        # Aggiungi la risposta corretta
        correct_letter = None
        for letter, (_, answer_text) in zip(['A', 'B', 'C', 'D'], shuffled_answers):
            if answer_text == question[correct_answer]:
                correct_letter = letter
                break

        base_prompt += f"\n\nLa risposta corretta è: {correct_letter}) {question[correct_answer]}"

        if additional_context:
            prompt = f"""
            Utilizzando il seguente contesto aggiuntivo:

            {additional_context}

            {base_prompt}

            Puoi fornire una spiegazione chiara e concisa (max 150 parole) del perché questa è la risposta corretta,
            facendo riferimento alle informazioni del contesto dove pertinente?
            """
        else:
            prompt = base_prompt + "\n\nPuoi fornire una spiegazione chiara e concisa (max 150 parole) del perché questa è la risposta corretta?"

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Errore nell'ottenere la spiegazione AI: {e}")
        return None



async def send_question_to_user(context, chat_id):
    question = get_random_question()

    answers = [
        (question['Risposta0'], '0'),
        (question['Risposta1'], '1'),
        (question['Risposta2'], '2'),
        (question['Risposta3'], '3')
    ]

    random.shuffle(answers)

    # Memorizza i dati specifici della domanda in user_data
    # Assicurati che user_data esista per questo chat_id
    if chat_id not in context.user_data:
        context.user_data[chat_id] = {}

    context.user_data[chat_id]['answer_mapping'] = {str(idx): original_idx for idx, (_, original_idx) in enumerate(answers)}
    context.user_data[chat_id]['correct_answer'] = question['RispostaCorretta']
    context.user_data[chat_id]['current_question'] = question

    message_text = f"Domanda:\n{question['Domanda']}\n\nRisposte:\n"
    for i, (answer_text, _) in enumerate(answers):
        message_text += f"{chr(65+i)}) {answer_text}\n"
    message_text += "\nSeleziona la tua risposta:"

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=get_keyboard()
        )
    except Exception as e:
        print(f"Errore nell'invio della domanda all'utente {chat_id}: {e}")


async def start(update, context):
    user = update.effective_user
    user_info = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    }

    is_new = add_user(user_info)

    welcome_message = (
        f'{"Benvenuto" if is_new else "Bentornato"} {user.first_name}!\n'
        "Riceverai domande sull'etica ogni ora.\n"
        "Usa /domanda per ricevere una nuova domanda.\n"
        "Usa /stop_domande per disattivare l'invio automatico delle domande."
    )

    await update.message.reply_text(welcome_message)

# Comando per ricevere una nuova domanda
async def command_domanda(update, context):
    await send_question_to_user(context, update.message.chat_id)

# Comando per fermare le domande automatiche
async def stop_domande(update, context):
    users = load_users()
    user_id = update.effective_user.id

    for user in users['users']:
        if user['id'] == user_id:
            user['reminders_enabled'] = False
            save_users(users)
            await update.message.reply_text("Invio automatico delle domande disattivato.\nUsa /domanda per ricevere domande quando vuoi.")
            return

    await update.message.reply_text("Si è verificato un errore. Prova a usare /start prima.")

# Comando per riattivare le domande automatiche
async def start_domande(update, context):
    users = load_users()
    user_id = update.effective_user.id

    for user in users['users']:
        if user['id'] == user_id:
            user['reminders_enabled'] = True
            save_users(users)
            await update.message.reply_text("Invio automatico delle domande riattivato!")
            return

    await update.message.reply_text("Si è verificato un errore. Prova a usare /start prima.")

# Funzione per inviare le domande periodiche
async def send_reminder(context):
    italy_tz = pytz.timezone('Europe/Rome')
    current_hour = datetime.now(italy_tz).hour

    if 9 <= current_hour < 23:
        users = load_users()
        for user in users['users']:
            if user.get('reminders_enabled', True):
                try:
                    await send_question_to_user(context, user['id'])
                except Exception as e:
                    print(f"Errore nell'invio del messaggio all'utente {user['id']}: {e}")

async def get_stats(update, context):
    user_id = str(update.effective_user.id)
    today = str(date.today())
    stats = load_stats()

    if user_id in stats and today in stats[user_id]:
        user_stats = stats[user_id][today]
        total_questions = user_stats["correct"] + user_stats["wrong"]
        correct_answers = user_stats["correct"]

        message = "📊 Statistiche di oggi:\n\n"
        message += f"Totale domande risposte: {total_questions}\n"
        message += f"Risposte corrette: {correct_answers}\n"
        message += f"Percentuale di successo: {(correct_answers/total_questions*100):.1f}%"
    else:
        message = "Non hai ancora risposto a nessuna domanda oggi!"

    await update.message.reply_text(message)

async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer() # È buona pratica rispondere subito al callback

    user_id = query.from_user.id

    # Recupera i dati specifici della domanda da user_data
    if user_id not in context.user_data or \
       'answer_mapping' not in context.user_data[user_id] or \
       'correct_answer' not in context.user_data[user_id] or \
       'current_question' not in context.user_data[user_id]:
        await query.edit_message_text(text="Si è verificato un errore o la domanda è scaduta. Prova con /domanda.")
        return

    user_question_data = context.user_data[user_id]
    answer_mapping = user_question_data['answer_mapping']
    correct_answer_key = user_question_data['correct_answer'] # Es. "Risposta1"
    current_question = user_question_data['current_question']

    if query.data.startswith('ans_'):
        selected_idx_str = query.data[4:]  # Ottiene l'indice selezionato come stringa ('0', '1', '2', '3')

        if selected_idx_str not in answer_mapping:
            await query.edit_message_text(text="Risposta non valida. Prova con /domanda.")
            return

        original_idx = answer_mapping[selected_idx_str] # Indice originale della risposta (0,1,2,3)
        selected_answer_key = f"Risposta{original_idx}" # Es. "Risposta2"

        is_correct = (selected_answer_key == correct_answer_key)
        result_message = "Corretto! 🎉" if is_correct else "Sbagliato! 😕"

        update_user_stats(user_id, is_correct)

        if AI_API and current_question:
            explanation = await get_ai_explanation(
                current_question,
                correct_answer_key, # Passa la chiave della risposta corretta
                answer_mapping
            )
            if explanation:
                result_message += f"\n\nSpiegazione:\n{explanation}"
        
        # Modifica il messaggio originale invece di inviarne uno nuovo
        # Rimuove anche la tastiera
        await query.edit_message_text(text=f"{query.message.text}\n\nLa tua risposta: {chr(65+int(selected_idx_str))}\n{result_message}", reply_markup=None)




def main():
    # Inizializza Gemini se l'API key è disponibile
    has_ai = setup_gemini()
    if has_ai:
        print("AI functionality enabled with Google Gemini")
    else:
        print("AI functionality disabled - No API key found")

    # Crea l'applicazione
    application = Application.builder().token(TOKEN).build()

    # Aggiungi gli handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("domanda", command_domanda))
    application.add_handler(CommandHandler("stop_domande", stop_domande))
    application.add_handler(CommandHandler("start_domande", start_domande))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("statistiche", get_stats))

    # Imposta il job per l'invio periodico delle domande
    job_queue = application.job_queue

    # Crea un array di orari per ogni 15 minuti tra le 9 e le 18
    times = []
    for hour in range(9, 22):
        for minute in [0]:
            times.append(time(hour, minute))

    # Programma i messaggi per ogni orario specificato
    for t in times:
        job_queue.run_daily(send_reminder, time=t, days=(0, 1, 2, 3, 4, 5, 6))

    # Aggiungi il job per l'invio delle statistiche giornaliere alle 21:00
    job_queue.run_daily(send_daily_stats, time=time(21, 0), days=(0, 1, 2, 3, 4, 5, 6))

    print("Bot avviato...")
    application.run_polling()

if __name__ == '__main__':
    main()
