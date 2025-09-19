// Configuración y variables globales
const API_BASE = '/api/v1';
let sessionId = 'web-' + Date.now();

// Referencias DOM (solo si existen)
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typing');
const statusElement = document.getElementById('status');

// Función para renderizar markdown
function renderMarkdown(text) {
    // Headers
    text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Bold y Strong
    text = text.replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>');
    text = text.replace(/__(.*?)__/gim, '<strong>$1</strong>');
    
    // Italic
    text = text.replace(/\*(.*?)\*/gim, '<em>$1</em>');
    text = text.replace(/_(.*?)_/gim, '<em>$1</em>');
    
    // Code inline
    text = text.replace(/`([^`]+)`/gim, '<code>$1</code>');
    
    // Code blocks
    text = text.replace(/```([^`]+)```/gim, '<pre><code>$1</code></pre>');
    
    // Links
    text = text.replace(/\[([^\]]+)\]\(([^\)]+)\)/gim, '<a href="$2" target="_blank" style="color: #ff8c42;">$1</a>');
    
    // Listas no ordenadas
    text = text.replace(/^\* (.+)$/gim, '<li>$1</li>');
    text = text.replace(/^- (.+)$/gim, '<li>$1</li>');
    text = text.replace(/^• (.+)$/gim, '<li>$1</li>');
    
    // Envolver listas en <ul>
    text = text.replace(/(<li>.*<\/li>)/s, function(match) {
        return '<ul>' + match + '</ul>';
    });
    
    // Listas ordenadas
    text = text.replace(/^\d+\. (.+)$/gim, '<li>$1</li>');
    
    // Blockquotes
    text = text.replace(/^> (.+)$/gim, '<blockquote>$1</blockquote>');
    
    // Párrafos (separar líneas dobles)
    text = text.replace(/\n\n/gim, '</p><p>');
    text = '<p>' + text + '</p>';
    
    // Limpiar párrafos vacíos y elementos mal formados
    text = text.replace(/<p><\/p>/gim, '');
    text = text.replace(/<p>(<h[1-6]>)/gim, '$1');
    text = text.replace(/(<\/h[1-6]>)<\/p>/gim, '$1');
    text = text.replace(/<p>(<ul>)/gim, '$1');
    text = text.replace(/(<\/ul>)<\/p>/gim, '$1');
    text = text.replace(/<p>(<ol>)/gim, '$1');
    text = text.replace(/(<\/ol>)<\/p>/gim, '$1');
    text = text.replace(/<p>(<blockquote>)/gim, '$1');
    text = text.replace(/(<\/blockquote>)<\/p>/gim, '$1');
    text = text.replace(/<p>(<pre>)/gim, '$1');
    text = text.replace(/(<\/pre>)<\/p>/gim, '$1');
    
    // Convertir saltos de línea simples a <br>
    text = text.replace(/\n/gim, '<br>');
    
    return text;
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Event listeners para input (solo si existe)
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Verificar estado del servidor al cargar
    checkServerStatus();
    
    // Auto-focus en el input (solo si existe)
    if (messageInput) {
        messageInput.focus();
    }
});

// Verificar estado del servidor
async function checkServerStatus() {
    // Solo verificar si el elemento de status existe (página de chat)
    if (!statusElement) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (data.status === 'ok') {
            statusElement.innerHTML = '🟢 Conectado al servidor Zabbix';
            statusElement.className = 'status-online';
        } else {
            statusElement.innerHTML = '🟡 Servidor en modo degradado';
            statusElement.className = 'status-offline';
        }
    } catch (error) {
        statusElement.innerHTML = '🔴 Sin conexión al servidor';
        statusElement.className = 'status-offline';
    }
}

// Enviar mensaje
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Deshabilitar input
    messageInput.disabled = true;
    sendButton.disabled = true;
    
    // Mostrar mensaje del usuario
    addMessage(message, 'user');
    messageInput.value = '';

    // Mostrar indicador de escritura
    showTyping();

    try {
        const response = await fetch(`${API_BASE}/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Ocultar indicador de escritura
        hideTyping();
        
        // Mostrar respuesta del bot con renderizado de markdown
        addMessage(data.response, 'bot', {
            dataSources: data.data_sources,
            queryTime: data.query_time,
            sqlQueries: data.sql_queries_executed
        });

    } catch (error) {
        hideTyping();
        addMessage(`Error: ${error.message}`, 'bot');
        console.error('Error sending message:', error);
    }

    // Rehabilitar input
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.focus();
}

// Agregar mensaje al chat
function addMessage(content, sender, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    if (sender === 'bot') {
        // Renderizar markdown
        let processedContent = renderMarkdown(content);
        
        // Detectar si hay información tabular (como hosts)
        if (content.includes('Host:') || content.includes('NOMBRE DEL HOST')) {
            processedContent = formatZabbixData(processedContent);
        }
        
        messageDiv.innerHTML = processedContent;
        
        // Agregar metadata si está disponible
        if (metadata.dataSources && metadata.dataSources.length > 0) {
            const metaDiv = document.createElement('div');
            metaDiv.style.marginTop = '12px';
            metaDiv.style.fontSize = '0.8rem';
            metaDiv.style.color = '#888888';
            metaDiv.style.borderTop = '1px solid #505050';
            metaDiv.style.paddingTop = '8px';
            
            metaDiv.innerHTML = `
                <strong>Fuentes:</strong> ${metadata.dataSources.join(', ')}<br>
                <strong>Tiempo:</strong> ${metadata.queryTime.toFixed(2)}s
            `;
            messageDiv.appendChild(metaDiv);
        }
    } else {
        messageDiv.textContent = content;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Formatear datos específicos de Zabbix
function formatZabbixData(content) {
    // Detectar y formatear listas de hosts
    if (content.includes('hosts activos') || content.includes('NOMBRE DEL HOST')) {
        // Extraer nombres de hosts de las respuestas
        const hostPattern = /([A-Z\s]+):\s*([^\n]+)/g;
        let matches;
        let hosts = [];
        
        while ((matches = hostPattern.exec(content)) !== null) {
            hosts.push(matches[2].trim());
        }
        
        if (hosts.length > 0) {
            let table = '<table><thead><tr><th>Host</th></tr></thead><tbody>';
            
            hosts.forEach(host => {
                table += `<tr><td>${host}</td></tr>`;
            });
            
            table += '</tbody></table>';
            
            return content.replace(/NOMBRE DEL HOST[\s\S]*$/, '') + table;
        }
    }
    
    return content;
}

// Mostrar indicador de escritura
function showTyping() {
    typingIndicator.style.display = 'block';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Ocultar indicador de escritura
function hideTyping() {
    typingIndicator.style.display = 'none';
}

// Limpiar chat
function clearChat() {
    const botMessages = messagesContainer.querySelectorAll('.message.bot');
    const userMessages = messagesContainer.querySelectorAll('.message.user');
    
    botMessages.forEach(msg => msg.remove());
    userMessages.forEach(msg => msg.remove());
    
    // Volver a mostrar mensaje de bienvenida
    const welcomeMessage = `¡Hola! Soy tu asistente especializado en Zabbix. 

Puedes preguntarme sobre:
• Estado de hosts y servicios
• Problemas activos y alertas
• Métricas y configuración
• Mejores prácticas de monitoreo

¿En qué puedo ayudarte hoy?`;
    
    addMessage(welcomeMessage, 'bot');
    
    // Nuevo session ID
    sessionId = 'web-' + Date.now();
}

// Funciones para el dashboard (si es necesario)
if (typeof loadDashboardStats !== 'undefined') {
    // Cargar estadísticas del dashboard
    async function loadDashboardStats() {
        try {
            const response = await fetch(`${API_BASE}/zabbix/status`);
            if (!response.ok) throw new Error('Error al cargar estadísticas');
            
            const stats = await response.json();
            updateDashboardUI(stats);
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }

    // Actualizar UI del dashboard
    function updateDashboardUI(stats) {
        // Actualizar valores de las tarjetas de estadísticas
        document.getElementById('total-hosts').textContent = stats.total_hosts || 0;
        document.getElementById('active-hosts').textContent = stats.active_hosts || 0;
        document.getElementById('total-items').textContent = stats.total_items || 0;
        document.getElementById('active-triggers').textContent = stats.active_triggers || 0;
    }
}