// src/frontend/src/App.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import { FaRobot, FaCopy, FaDownload, FaRegCopy } from 'react-icons/fa'; 

function App() {
  const [pdf, setPdf] = useState(null);
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [pdfId, setPdfId] = useState('');
  const [loading, setLoading] = useState(false);
  
  const chatEndRef = useRef(null);

  const BACKEND_URL = 'http://localhost:8000';


  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!pdf) {
      alert('Por favor, selecione um arquivo PDF.');
      return;
    }

    const formData = new FormData();
    formData.append('file', pdf);

    setLoading(true);

    try {
      const res = await axios.post(`${BACKEND_URL}/upload-pdf/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setPdfId(res.data.pdf_id);
      setChatHistory([]);
      alert('PDF enviado com sucesso!');
    } catch (error) {
      console.error(error);
      alert('Erro ao enviar PDF.');
    }

    setLoading(false);
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question) {
      alert('Por favor, digite uma pergunta.');
      return;
    }

    if (!pdfId) {
      alert('Por favor, faça upload de um PDF primeiro.');
      return;
    }
      
    setLoading(true);

    try {
      const res = await axios.post(`${BACKEND_URL}/ask/`, {
        pdf_id: pdfId,
        question: question,
      });
      console.log(res.data);
      setChatHistory([...chatHistory, { 
        type: 'user', 
        message: question 
      }, { 
        type: 'ai', 
        resposta: res.data.resposta, 
        explicação: res.data.explicação,
        json: res.data
      }]);
      setQuestion('');
    } catch (error) {
      console.error(error);
      alert('Erro ao fazer pergunta.');
    }

    setLoading(false);
  };

  const handleCopyJSON = (jsonData) => {
    const jsonString = JSON.stringify(jsonData, null, 2);
    navigator.clipboard.writeText(jsonString)
      .then(() => {
        alert('Resposta JSON copiada para a área de transferência!');
      })
      .catch((err) => {
        console.error('Erro ao copiar:', err);
        alert('Erro ao copiar a resposta JSON.');
      });
  };

  const handleDownloadJSON = (jsonData) => {
    const jsonString = JSON.stringify(jsonData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `resposta_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyText = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        alert('Texto copiado para a área de transferência!');
      })
      .catch((err) => {
        console.error('Erro ao copiar:', err);
        alert('Erro ao copiar o texto.');
      });
  };

  return (
    <div className="App">
      <header>
        <FaRobot className="header-icon" />
        <h1>Upload de PDF e Chat com IA</h1>
      </header>
      
      <main>
        <div className="chat-container">
          <div className="chat-history">
            {chatHistory.map((chat, index) => (
              chat.type === 'user' ? (
                <div key={index} className="chat-entry user-message">
                  <p><strong>Pergunta:</strong> {chat.message}</p>
                </div>
              ) : (
                <div key={index} className="chat-entry ai-message">
                  <p><strong>Resposta:</strong> {chat.resposta}</p>
                  <p><strong>Explicação:</strong> {chat.explicação}</p>
                  <div className="action-buttons"> {}
                    <FaRegCopy 
                      className="icon-button copy-text" 
                      title="Copiar Texto" 
                      onClick={() => handleCopyText(chat.resposta)} 
                    />
                    <FaCopy 
                      className="icon-button" 
                      title="Copiar JSON" 
                      onClick={() => handleCopyJSON(chat.json)} 
                    />
                    <FaDownload 
                      className="icon-button" 
                      title="Baixar JSON" 
                      onClick={() => handleDownloadJSON(chat.json)} 
                    />
                  </div>
                </div>
              )
            ))}
            <div ref={chatEndRef} />
          </div>
        </div>

        <div className="forms-container">
          <form onSubmit={handleUpload} className="upload-form">
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setPdf(e.target.files[0])}
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Enviando...' : 'Enviar PDF'}
            </button>
          </form>

          {pdfId && (
            <form onSubmit={handleAsk} className="ask-form">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Faça sua pergunta sobre o PDF..."
                required
              />
              <button type="submit" disabled={loading}>
                {loading ? 'Perguntando...' : 'Perguntar'}
              </button>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
