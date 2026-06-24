// gère les éléments communs de l'interface
import React from 'react';
import { FaRobot, FaHeartbeat, FaHome, FaSignOutAlt, FaUserCircle } from 'react-icons/fa';
import { MdHealthAndSafety } from 'react-icons/md';
import StatusBadge from './StatusBadge';

const TAB_ACTIVE_CLASSES = {
  home: 'bg-white text-primary-700 shadow-md',
  chat: 'bg-white text-primary-700 shadow-md',
  iot: 'bg-white text-mental-700 shadow-md',
};

const TABS = [
  { id: 'home', label: 'Accueil', icon: FaHome },
  { id: 'chat', label: 'Assistant médical', icon: FaRobot },
  { id: 'iot', label: 'Surveillance IoT', icon: FaHeartbeat },
];

const Navbar = ({ activeTab, setActiveTab, serverStatus, user, onLogout }) => {
  return (
    <nav className="sticky top-0 z-20 bg-gradient-to-r from-primary-800 to-primary-600 shadow-lg">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 py-3 sm:h-16 sm:flex-row sm:items-center sm:justify-between sm:py-0">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <MdHealthAndSafety className="text-3xl text-white" />
              <span className="text-lg font-bold text-white sm:text-xl">Multi-Agents Santé</span>
              <span className="rounded-full bg-white/15 px-2 py-0.5 text-[10px] font-medium text-white sm:text-xs">v4.0</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 sm:justify-end sm:gap-4">
            <div className="flex gap-1 sm:gap-2">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 sm:px-4 ${
                      isActive ? TAB_ACTIVE_CLASSES[tab.id] : 'text-white/80 hover:bg-white/10 hover:text-white'
                    }`}
                  >
                    <Icon />
                    <span className="hidden sm:inline">{tab.label}</span>
                    <span className="sm:hidden">{tab.id === 'home' ? 'Accueil' : tab.id === 'chat' ? 'Chat' : 'IoT'}</span>
                  </button>
                );
              })}
            </div>

            <div className="hidden items-center gap-3 lg:flex">
              <StatusBadge status={serverStatus?.user_server} label="Assistant" />
              <StatusBadge status={serverStatus?.iot_server} label="IoT" />
            </div>

            <div className="flex items-center gap-2 rounded-xl bg-white/10 px-3 py-2 text-sm text-white">
              <FaUserCircle />
              <span className="hidden max-w-[140px] truncate sm:inline">{user?.name}</span>
              <button
                type="button"
                onClick={onLogout}
                className="ml-1 rounded-lg p-1 text-white/80 hover:bg-white/10 hover:text-white"
                title="Déconnexion"
              >
                <FaSignOutAlt />
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
