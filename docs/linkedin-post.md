# LinkedIn post draft

## Versione italiana

Ho sviluppato **AI Knowledge Assistant**, un assistente conversazionale basato su RAG per interrogare documenti PDF con fonti verificabili.

L’obiettivo non era creare una semplice chat con un LLM, ma progettare un piccolo sistema AI con caratteristiche vicine a un’applicazione reale:

- API REST con FastAPI;
- interfaccia Streamlit;
- upload, chunking e indicizzazione di PDF;
- embeddings e ricerca semantica;
- risposte grounded con citazioni di documento e pagina;
- cronologia conversazioni persistente;
- architettura a porte e adapter per sostituire il provider LLM;
- test automatici, type checking, linting e CI su GitHub Actions.

Una parte importante del lavoro è stata la validazione. Ho testato separatamente:

- comportamento del dominio e del servizio RAG;
- endpoint FastAPI e contratti HTTP;
- upload e indicizzazione end-to-end;
- persistenza della cronologia e delle citazioni dopo un refresh;
- comportamento in caso di domande fuori tema;
- errori di provider e configurazione;
- qualità del retrieval con metriche Hit@K e MRR.

Durante lo sviluppo ho anche diagnosticato e risolto problemi reali, tra cui:

- errori mypy causati da dipendenze opzionali;
- differenze tra path Windows e Linux nella CI;
- timeout dovuti a tentativi di accesso alla rete durante il caricamento degli embeddings;
- mismatch tra dimensioni degli embeddings;
- falsi recuperi semantici per domande non presenti nei documenti;
- perdita delle citazioni dopo il reload della conversazione.

Il sistema rifiuta esplicitamente le risposte quando non trova evidenze sufficienti, restituendo:

> Informazione non trovata nei documenti.

Per mantenere il progetto gratuito e leggero, il default locale usa un provider mock deterministico e un’architettura pronta per integrare in futuro OpenRouter, Amazon Bedrock, OpenAI o Anthropic senza modificare la logica applicativa.

Questo progetto mi ha permesso di approfondire Python, LangChain, RAG, FastAPI, testing, CI/CD e principi di Clean Architecture applicati a sistemi AI.

Repository: https://github.com/RoccoDatena/AI-Knowledge-Assistant-LangChain-RAG-

#AIEngineering #GenerativeAI #RAG #LangChain #Python #FastAPI #MachineLearning #SoftwareArchitecture

## Suggerimenti per la pubblicazione

- Allegare uno screenshot della UI principale.
- Allegare, se possibile, una seconda immagine con una risposta grounded e le citazioni visibili.
- Mantenere il link al repository alla fine del post.
- Non pubblicare API key, file `.env`, documenti PDF personali o dati presenti nella cartella `data/`.
- Presentare il post come progetto portfolio in evoluzione, non come prodotto SaaS già pronto per traffico production.
