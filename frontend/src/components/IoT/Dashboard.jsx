// gère l'affichage des données de santé
import React, { useState, useEffect, useCallback } from 'react';
import {
  FaHeartbeat,
  FaLungs,
  FaTachometerAlt,
  FaThermometerHalf,
  FaChartLine,
  FaTrash,
} from 'react-icons/fa';
import VitalSignsChart from './VitalSignsChart';
import AlertPanel from './AlertPanel';
import healthAPI from '../../services/api';
import toast from 'react-hot-toast';

const MAX_POINTS = 30;

const POLL_INTERVAL_MS = Number(process.env.REACT_APP_POLL_INTERVAL_MS) || 15 * 1000;
const NORMAL_RANGES = {
  heart_rate:         { min: 40,  max: 130, unit: 'bpm'  },
  spo2:               { min: 90,  max: 100, unit: '%'    },
  blood_pressure_sys: { min: 80,  max: 180, unit: 'mmHg' },
  blood_pressure_dia: { min: 50,  max: 120, unit: 'mmHg' },
  temperature:        { min: 35.0,max: 39.5,unit: '°C'   },
};
const isAbnormal = (metric, value) => {
  const range = NORMAL_RANGES[metric];
  if (!range || value === null || value === undefined) return false;
  return value < range.min || value > range.max;
};

const toDataPoint = (row) => ({
  id:                 row.id ?? Date.now(),
  timestamp:          new Date(row.timestamp || row.received_at || Date.now()),
  heart_rate:         row.heart_rate         ?? row.vitals?.heart_rate         ?? null,
  spo2:               row.spo2               ?? row.vitals?.spo2               ?? null,
  blood_pressure_sys: row.blood_pressure_sys ?? row.vitals?.blood_pressure_sys ?? null,
  blood_pressure_dia: row.blood_pressure_dia ?? row.vitals?.blood_pressure_dia ?? null,
  temperature:        row.temperature        ?? row.vitals?.temperature        ?? null,
});

const Dashboard = ({ user }) => {
  const PATIENT_ID = user?.patient_id || 'patient_001';
  const [realTimeData, setRealTimeData] = useState([]);
  const [alerts, setAlerts]             = useState([]);
  const [lastUpdated, setLastUpdated]   = useState(null);


  useEffect(() => {
    const loadHistory = async () => {
      const result = await healthAPI.getIoTHistory(PATIENT_ID, 1);
      if (result?.measurements?.length) {
        const points = result.measurements.map(toDataPoint).slice(-MAX_POINTS);
        setRealTimeData(points);
        setLastUpdated(new Date());
      }
    };
    loadHistory();
  }, [PATIENT_ID]);


  const fetchLatest = useCallback(async () => {
    const result = await healthAPI.getLatestIoTData(PATIENT_ID);
    if (!result?.vitals) return;

    const point = toDataPoint(result);

    setRealTimeData((prev) => {

      const lastTs = prev[prev.length - 1]?.timestamp?.getTime();
      if (lastTs && point.timestamp.getTime() === lastTs) return prev;
      return [...prev, point].slice(-MAX_POINTS);
    });
    setLastUpdated(new Date());


    if (result.status === 'anomaly' && result.alert) {
      setAlerts((prev) => {

        if (prev.some((a) => a.timestamp?.getTime() === point.timestamp.getTime())) return prev;
        const newAlert = {
          id:         Date.now(),
          timestamp:  point.timestamp,
          patientId:  PATIENT_ID,
          anomalies:  result.anomalies,
          message:    result.alert,
          read:       false,
        };
        toast.error('Alerte santé détectée', { duration: 8000, icon: '🚨' });
        return [newAlert, ...prev].slice(0, 30);
      });
    }
  }, [PATIENT_ID]);


  useEffect(() => {
    fetchLatest();
    const interval = setInterval(fetchLatest, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchLatest]);

  const getLatestValue = (metric) => {
    if (realTimeData.length === 0) return null;
    return realTimeData[realTimeData.length - 1][metric];
  };

  const clearData = () => setRealTimeData([]);

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-4 sm:p-6">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-800 sm:text-2xl">
            <FaChartLine className="text-primary-500" />
            Surveillance Santé — Données Connectées
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Surveillance continue des constantes vitales
            {lastUpdated && (
              <span className="ml-2 text-gray-400">
                — Mise à jour : {lastUpdated.toLocaleTimeString('fr-FR')}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={clearData}
          disabled={realTimeData.length === 0}
          className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-500 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <FaTrash />
          Réinitialiser
        </button>
      </div>

      <div className="mb-6">
        <AlertPanel
          alerts={alerts}
          onDismiss={(id) =>
            setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, read: true } : a)))
          }
          onDismissAll={() => setAlerts((prev) => prev.map((a) => ({ ...a, read: true })))}
          onClearAll={() => setAlerts([])}
        />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <VitalCard
          icon={FaHeartbeat}
          label="Fréquence cardiaque"
          value={getLatestValue('heart_rate')}
          unit="bpm"
          accent="border-primary-500 text-primary-500"
          abnormal={isAbnormal('heart_rate', getLatestValue('heart_rate'))}
        />
        <VitalCard
          icon={FaLungs}
          label="Saturation O₂"
          value={getLatestValue('spo2')}
          unit="%"
          accent="border-mental-500 text-mental-500"
          abnormal={isAbnormal('spo2', getLatestValue('spo2'))}
        />
        <VitalCard
          icon={FaTachometerAlt}
          label="Pression artérielle"
          value={
            getLatestValue('blood_pressure_sys') !== null
              ? `${getLatestValue('blood_pressure_sys')}/${getLatestValue('blood_pressure_dia')}`
              : null
          }
          unit="mmHg"
          accent="border-pharmacy-500 text-pharmacy-500"
          abnormal={
            isAbnormal('blood_pressure_sys', getLatestValue('blood_pressure_sys')) ||
            isAbnormal('blood_pressure_dia', getLatestValue('blood_pressure_dia'))
          }
        />
        <VitalCard
          icon={FaThermometerHalf}
          label="Température"
          value={getLatestValue('temperature')}
          unit="°C"
          accent="border-nutrition-500 text-nutrition-500"
          abnormal={isAbnormal('temperature', getLatestValue('temperature'))}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <VitalSignsChart
          data={realTimeData}
          series={[{ key: 'heart_rate', name: 'FC', color: '#0ea5e9', unit: 'bpm' }]}
          title="Fréquence cardiaque"
          normalRange={NORMAL_RANGES.heart_rate}
        />
        <VitalSignsChart
          data={realTimeData}
          series={[{ key: 'spo2', name: 'SpO₂', color: '#10b981', unit: '%' }]}
          title="Saturation en oxygène"
          normalRange={NORMAL_RANGES.spo2}
        />
        <VitalSignsChart
          data={realTimeData}
          series={[
            { key: 'blood_pressure_sys', name: 'Systolique', color: '#f43f5e', unit: 'mmHg' },
            { key: 'blood_pressure_dia', name: 'Diastolique', color: '#fb923c', unit: 'mmHg' },
          ]}
          title="Pression artérielle"
          normalRange={NORMAL_RANGES.blood_pressure_sys}
        />
        <VitalSignsChart
          data={realTimeData}
          series={[{ key: 'temperature', name: 'Température', color: '#f97316', unit: '°C' }]}
          title="Température corporelle"
          normalRange={NORMAL_RANGES.temperature}
        />
      </div>
    </div>
  );
};

const VitalCard = ({ icon: Icon, label, value, unit, accent, abnormal }) => {
  const [borderClass, iconClass] = accent.split(' ');
  return (
    <div className={`rounded-xl border-l-4 bg-white p-4 shadow-sm ${borderClass}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="flex items-center gap-2 text-sm text-gray-500">
            {label}
            {value !== null && (
              <span
                className={`inline-block h-2 w-2 rounded-full ${
                  abnormal ? 'bg-red-500' : 'bg-emerald-500'
                }`}
                title={abnormal ? 'Valeur hors plage normale' : 'Valeur dans la plage normale'}
              />
            )}
          </p>
          <p className="text-2xl font-bold text-gray-800">
            {value ?? '—'} <span className="text-sm font-normal">{unit}</span>
          </p>
        </div>
        <Icon className={`text-3xl ${iconClass}`} />
      </div>
    </div>
  );
};

export default Dashboard;
