// regroupe les appels vers le backend
import axios from 'axios';
import toast from 'react-hot-toast';


const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';


const PIPELINE_TIMEOUT_MS = 30 * 60 * 1000;
const HEALTHCHECK_TIMEOUT_MS = 4000;

class HealthAPI {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: PIPELINE_TIMEOUT_MS,
      headers: {
        'Content-Type': 'application/json',
      },
    });


    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        return Promise.reject(this._normalizeError(error));
      }
    );
  }

  _normalizeError(error) {
    if (error.response) {

      const detail = error.response.data?.detail;
      return new Error(
        typeof detail === 'string'
          ? detail
          : `Erreur ${error.response.status} : le serveur n'a pas pu traiter la demande.`
      );
    }
    if (error.code === 'ECONNABORTED') {
      return new Error(
        "Le pipeline d'agents dépasse 15 minutes, ce qui est anormalement long. Le backend a peut-être rencontré un problème (boucle manager/évaluateur, LLM bloqué). Vérifiez les logs du serveur."
      );
    }
    if (error.request) {
      return new Error(
        `Impossible de contacter le serveur (${API_BASE_URL}). Vérifiez que le backend est démarré (python main.py).`
      );
    }
    return new Error(error.message || 'Erreur inconnue.');
  }


async register(name, email, password) {
  const response = await this.client.post('/auth/register', { name, email, password });
  return response.data;
}

async login(email, password) {
  const response = await this.client.post('/auth/login', { email, password });
  return response.data;
}

async getMe(userId) {
  const response = await this.client.get(`/auth/me/${userId}`);
  return response.data;
}

async forgotPassword(email) {
  const response = await this.client.post('/auth/forgot-password', { email });
  return response.data;
}

async resetPassword(email, token, newPassword) {
  const response = await this.client.post('/auth/reset-password', {
    email,
    token,
    new_password: newPassword,
  });
  return response.data;
}

async getSmtpStatus() {
  const response = await this.client.get('/auth/smtp-status', { timeout: HEALTHCHECK_TIMEOUT_MS });
  return response.data;
}

async sendTestEmail(email) {
  const response = await this.client.post('/auth/test-email', { email });
  return response.data;
}


  async healthCheck() {
    try {
      const response = await this.client.get('/health', {
        timeout: HEALTHCHECK_TIMEOUT_MS,
      });
      return response.data;
    } catch (error) {
      return null;
    }
  }

  async getSubServersStatus() {
    const data = await this.healthCheck();
    return data?.sub_servers ?? null;
  }


  async askQuestion(question, userId = 'user_001', conversationId = null) {
    try {
      const response = await this.client.post('/ask', {
        question,
        user_id: userId,
        conversation_id: conversationId,
      });
      return response.data;
    } catch (error) {
      toast.error(error.message);
      throw error;
    }
  }


  async getConversations(userId = 'user_001') {
    try {
      const response = await this.client.get('/conversations', {
        params: { user_id: userId },
        timeout: HEALTHCHECK_TIMEOUT_MS,
      });
      return response.data?.conversations ?? [];
    } catch {
      return [];
    }
  }


  async getConversationMessages(conversationId, userId = null) {
    const response = await this.client.get(`/conversations/${conversationId}/messages`, {
      params: userId ? { user_id: userId } : {},
    });
    return response.data;
  }


  async renameConversation(conversationId, title) {
    try {
      const response = await this.client.patch(`/conversations/${conversationId}`, { title });
      return response.data;
    } catch (error) {
      toast.error(error.message);
      throw error;
    }
  }


  async deleteConversation(conversationId, userId = null) {
    try {
      const response = await this.client.delete(`/conversations/${conversationId}`, {
        params: userId ? { user_id: userId } : {},
      });
      return response.data;
    } catch (error) {
      toast.error(error.message);
      throw error;
    }
  }


  async sendIoTData(data) {
    try {
      const response = await this.client.post('/iot/data', data);
      return response.data;
    } catch (error) {
      toast.error(error.message);
      throw error;
    }
  }


  async getLatestIoTData(patientId = 'patient_001') {
    try {
      const response = await this.client.get(`/iot/latest/${patientId}`, {
        timeout: HEALTHCHECK_TIMEOUT_MS,
      });
      return response.data;
    } catch {
      return null;
    }
  }


  async getIoTHistory(patientId = 'patient_001', days = 1) {
    try {
      const response = await this.client.get(`/iot/history/${patientId}`, {
        params: { days },
        timeout: HEALTHCHECK_TIMEOUT_MS,
      });
      return response.data;
    } catch {
      return null;
    }
  }

}

const healthAPI = new HealthAPI();

export default healthAPI;
