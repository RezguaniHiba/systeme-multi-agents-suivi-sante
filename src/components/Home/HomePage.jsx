// contient le code du module
import React from 'react';
import { FaRobot, FaHeartbeat, FaArrowRight } from 'react-icons/fa';

const Card = ({ icon: Icon, title, description, onClick }) => (
  <button
    onClick={onClick}
    className="group rounded-2xl bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:shadow-xl"
  >
    <div className="mb-4 inline-flex rounded-xl bg-primary-50 p-3 text-primary-600">
      <Icon className="text-2xl" />
    </div>
    <h3 className="text-lg font-bold text-gray-800">{title}</h3>
    <p className="mt-2 text-sm leading-6 text-gray-500">{description}</p>
    <div className="mt-4 flex items-center gap-2 text-sm font-semibold text-primary-600">
      Ouvrir <FaArrowRight className="transition group-hover:translate-x-1" />
    </div>
  </button>
);

const HomePage = ({ user, onNavigate }) => {
  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl">
        <div className="rounded-3xl bg-gradient-to-r from-primary-700 to-mental-600 p-8 text-white shadow-lg">
          <p className="text-sm font-semibold uppercase tracking-wide text-white/70">Bienvenue</p>
          <h1 className="mt-2 text-3xl font-extrabold sm:text-4xl">
            Bonjour {user?.name || 'utilisateur'} 👋
          </h1>
          <p className="mt-3 max-w-2xl text-white/90">
            Connectez-vous, posez vos questions à un assistant médical multi-agents et surveillez les données IoT de votre patient connecté.
          </p>
          <p className="mt-2 text-sm text-white/75">
            Patient associé : <span className="font-bold text-white">{user?.patient_id}</span>
          </p>
        </div>

        <div className="mt-8 grid gap-5 md:grid-cols-2">
          <Card
            icon={FaRobot}
            title="Conversation avec l’assistant"
            description="Posez une question de santé à un assistant médical multi-agents : orientation, conseils généraux, nutrition ou bien-être mental."
            onClick={() => onNavigate('chat')}
          />
          <Card
            icon={FaHeartbeat}
            title="Surveillance médicale IoT"
            description="Suivez les constantes vitales envoyées par la smartwatch et consultez les alertes détectées automatiquement."
            onClick={() => onNavigate('iot')}
          />
        </div>
      </div>
    </div>
  );
};

export default HomePage;
