// gère les écrans de connexion et d'inscription
import React, { useEffect, useState } from 'react';
import { FaHeartbeat, FaUserPlus, FaSignInAlt, FaKey } from 'react-icons/fa';
import toast from 'react-hot-toast';
import healthAPI from '../../services/api';

const AuthPage = ({ onAuthenticated }) => {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    resetToken: '',
    newPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [resetInfo, setResetInfo] = useState(null);

  const isRegister = mode === 'register';
  const isForgot = mode === 'forgot';
  const isReset = mode === 'reset';

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('reset_token');
    const email = params.get('email');
    if (token) {
      setMode('reset');
      setForm((prev) => ({
        ...prev,
        email: email || prev.email,
        resetToken: token,
      }));
    }
  }, []);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const switchMode = (nextMode) => {
    setMode(nextMode);
    setResetInfo(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResetInfo(null);

    try {
      if (isForgot) {
        const result = await healthAPI.forgotPassword(form.email);
        setResetInfo(result);

        if (result?.email_sent) {
          toast.success('Email de réinitialisation envoyé. Vérifiez votre boîte mail.');
        } else if (result?.reset_token_preview) {
          toast('SMTP non configuré : lien de test affiché en mode développement.', { icon: 'ℹ️' });
          setForm((prev) => ({
            ...prev,
            resetToken: result.reset_token_preview,
          }));
          setMode('reset');
        } else {
          toast.success('Si cet email existe, un lien de réinitialisation a été envoyé.');
        }
        return;
      }

      if (isReset) {
        const result = await healthAPI.resetPassword(
          form.email,
          form.resetToken,
          form.newPassword
        );
        onAuthenticated(result.user, result.token);
        toast.success('Mot de passe réinitialisé avec succès.');
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }

      const result = isRegister
        ? await healthAPI.register(form.name, form.email, form.password)
        : await healthAPI.login(form.email, form.password);

      onAuthenticated(result.user, result.token);
      toast.success(isRegister ? 'Compte créé avec succès.' : 'Connexion réussie.');
    } catch (error) {
      toast.error(error.message || 'Erreur d’authentification.');
    } finally {
      setLoading(false);
    }
  };

  const getTitle = () => {
    if (isRegister) return 'Créer un compte';
    if (isForgot) return 'Mot de passe oublié';
    if (isReset) return 'Nouveau mot de passe';
    return 'Se connecter';
  };

  const getSubtitle = () => {
    if (isRegister) return 'Créez votre espace pour utiliser l’assistant médical et la surveillance IoT.';
    if (isForgot) return 'Saisissez votre email pour recevoir un lien de réinitialisation.';
    if (isReset) return 'Saisissez le code reçu par email et choisissez un nouveau mot de passe.';
    return 'Accédez à votre espace de suivi santé intelligent.';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-800 via-primary-600 to-mental-600 px-4 py-10">
      <div className="mx-auto grid min-h-[80vh] max-w-6xl items-center gap-8 lg:grid-cols-2">
        <div className="text-white">
          <div className="mb-5 inline-flex items-center gap-3 rounded-2xl bg-white/15 px-4 py-3 shadow-lg backdrop-blur">
            <FaHeartbeat className="text-3xl" />
            <span className="text-xl font-bold">Multi-Agents Santé</span>
          </div>
          <h1 className="text-4xl font-extrabold leading-tight sm:text-5xl">
            Assistant médical intelligent et surveillance IoT connectée.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-white/90">
            Posez vos questions de santé à un assistant médical multi-agents et surveillez vos constantes vitales en temps réel grâce aux données IoT. L’application fournit des conseils clairs et des alertes lorsqu’une anomalie est détectée.
          </p>
          <div className="mt-8 grid max-w-xl gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-white/15 p-4 backdrop-blur">Assistant médical multi-agents</div>
            <div className="rounded-xl bg-white/15 p-4 backdrop-blur">Surveillance médicale IoT</div>
          </div>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-2xl sm:p-8">
          {!isForgot && !isReset && (
            <div className="mb-6 flex rounded-xl bg-gray-100 p-1">
              <button
                type="button"
                onClick={() => switchMode('login')}
                className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${!isRegister ? 'bg-white text-primary-700 shadow' : 'text-gray-500'}`}
              >
                <FaSignInAlt /> Connexion
              </button>
              <button
                type="button"
                onClick={() => switchMode('register')}
                className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${isRegister ? 'bg-white text-primary-700 shadow' : 'text-gray-500'}`}
              >
                <FaUserPlus /> Inscription
              </button>
            </div>
          )}

          <div className="mb-6 flex items-start gap-3">
            {(isForgot || isReset) && (
              <div className="rounded-xl bg-primary-50 p-3 text-primary-700">
                <FaKey />
              </div>
            )}
            <div>
              <h2 className="text-2xl font-bold text-gray-800">{getTitle()}</h2>
              <p className="mt-1 text-sm text-gray-500">{getSubtitle()}</p>
            </div>
          </div>

          {resetInfo?.email_sent && (
            <div className="mb-4 rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-800">
              <p className="font-semibold">Email envoyé.</p>
              <p className="mt-1">Vérifiez votre boîte mail et vos spams.</p>
            </div>
          )}

          {resetInfo?.reset_link_preview && (
            <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
              <p className="font-semibold">Mode développement : SMTP Brevo n’est pas configuré ou l’email n’existe pas.</p>
              <p className="mt-1 break-all">Lien de test : {resetInfo.reset_link_preview}</p>
            </div>
          )}

          {resetInfo?.debug && (
            <div className="mb-4 rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
              <p className="font-semibold">Debug :</p>
              <p className="mt-1">{resetInfo.debug}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Nom complet</label>
                <input
                  value={form.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Votre nom"
                  required
                />
              </div>
            )}

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => updateField('email', e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="email@example.com"
                required
              />
            </div>

            {!isForgot && !isReset && (
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Mot de passe</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => updateField('password', e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Minimum 6 caractères"
                  minLength={6}
                  required
                />
              </div>
            )}

            {isReset && (
              <>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Code de réinitialisation</label>
                  <input
                    value={form.resetToken}
                    onChange={(e) => updateField('resetToken', e.target.value)}
                    className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Code reçu par email"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Nouveau mot de passe</label>
                  <input
                    type="password"
                    value={form.newPassword}
                    onChange={(e) => updateField('newPassword', e.target.value)}
                    className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Minimum 6 caractères"
                    minLength={6}
                    required
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-primary-600 px-4 py-3 font-semibold text-white shadow-lg transition hover:bg-primary-700 disabled:opacity-60"
            >
              {loading
                ? 'Veuillez patienter…'
                : isForgot
                  ? 'Envoyer le lien'
                  : isReset
                    ? 'Réinitialiser le mot de passe'
                    : isRegister
                      ? 'Créer mon compte'
                      : 'Connexion'}
            </button>
          </form>

          <div className="mt-5 space-y-2 text-center text-sm">
            {!isRegister && !isForgot && !isReset && (
              <button
                type="button"
                onClick={() => switchMode('forgot')}
                className="font-medium text-primary-700 hover:underline"
              >
                Mot de passe oublié ?
              </button>
            )}

            {(isForgot || isReset) && (
              <button
                type="button"
                onClick={() => switchMode('login')}
                className="font-medium text-primary-700 hover:underline"
              >
                Retour à la connexion
              </button>
            )}

            {isForgot && (
              <div>
                <button
                  type="button"
                  onClick={() => switchMode('reset')}
                  className="text-gray-500 hover:text-primary-700 hover:underline"
                >
                  J’ai déjà un code de réinitialisation
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
