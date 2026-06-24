# simule les mesures envoyées par la montre
import requests
import time
import random
import argparse
from datetime import datetime, timezone


def generate_normal_data() -> dict:
    return {
        "heart_rate": round(random.uniform(60, 90), 1),
        "spo2": round(random.uniform(96, 99), 1),
        "blood_pressure_sys": round(random.uniform(110, 130), 1),
        "blood_pressure_dia": round(random.uniform(70, 85), 1),
        "temperature": round(random.uniform(36.3, 37.3), 1),
    }


def generate_anomaly_data() -> dict:
    data = generate_normal_data()

    anomaly_type = random.choice([
        "tachycardia",
        "bradycardia",
        "low_spo2",
        "hypertension",
        "hypothermia",
        "hyperthermia",
    ])

    if anomaly_type == "tachycardia":
        data["heart_rate"] = round(random.uniform(131, 180), 1)
        print(f"    ⚠️ Anomalie simulée : Tachycardie ({data['heart_rate']} bpm)")

    elif anomaly_type == "bradycardia":
        data["heart_rate"] = round(random.uniform(30, 39), 1)
        print(f"    ⚠️ Anomalie simulée : Bradycardie ({data['heart_rate']} bpm)")

    elif anomaly_type == "low_spo2":
        data["spo2"] = round(random.uniform(84, 89), 1)
        print(f"    ⚠️ Anomalie simulée : SpO2 basse ({data['spo2']}%)")

    elif anomaly_type == "hypertension":
        data["blood_pressure_sys"] = round(random.uniform(181, 200), 1)
        print(
            f"    ⚠️ Anomalie simulée : Hypertension systolique "
            f"({data['blood_pressure_sys']} mmHg)"
        )

    elif anomaly_type == "hypothermia":
        data["temperature"] = round(random.uniform(33.0, 34.9), 1)
        print(f"    ⚠️ Anomalie simulée : Hypothermie ({data['temperature']}°C)")

    elif anomaly_type == "hyperthermia":
        data["temperature"] = round(random.uniform(39.6, 41.0), 1)
        print(f"    ⚠️ Anomalie simulée : Hyperthermie ({data['temperature']}°C)")

    return data

def generate_anomaly_data() -> dict:
    data = generate_normal_data()

    data["heart_rate"] = 150

    print(f"    ⚠️ Anomalie simulée : Tachycardie ({data['heart_rate']} bpm)")

    return data

def generate_data(mode: str) -> dict:
    if mode == "normal":
        return generate_normal_data()

    if mode == "anomaly":
        return generate_anomaly_data()


    return generate_anomaly_data() if random.random() < 0.25 else generate_normal_data()


def display_response_status(result: dict) -> None:
    status = result.get("status", "?")

    if status == "pending":
        print("   ⏳ Statut : PENDING — données enregistrées, analyse CrewAI en cours")

    elif status == "normal":
        print("   ✅ Statut : NORMAL — aucune alerte")

    elif status == "anomaly":
        anomalies = result.get("anomalies", [])
        alert = result.get("alert", "")

        print("   ⚠️ Statut : ANOMALIE")
        print(f"   Anomalies : {anomalies}")
        print(f"   Alerte :\n{alert}")

    elif status == "error":
        alert = result.get("alert", "")
        print("   ❌ Statut : ERROR — erreur dans le pipeline")
        if alert:
            print(f"   Détail : {alert}")

    else:
        print(f"   ℹ️ Statut reçu : {status}")
        print(f"   Réponse serveur : {result}")


def send_data(url: str, patient_id: str, mode: str) -> None:
    data = generate_data(mode)
    data["patient_id"] = patient_id
    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    print(f"\n📡 [{data['timestamp'][:19]}] Envoi des données...")
    print(
        f"   FC={data['heart_rate']} bpm | "
        f"SpO2={data['spo2']}% | "
        f"PA={data['blood_pressure_sys']}/{data['blood_pressure_dia']} mmHg | "
        f"T°={data['temperature']}°C"
    )

    try:
        response = requests.post(url, json=data, timeout=600)
        response.raise_for_status()
        result = response.json()

        display_response_status(result)

    except requests.exceptions.ConnectionError:
        print(f"   ❌ Impossible de joindre l'API ({url}). Vérifiez que le serveur est démarré.")

    except requests.exceptions.Timeout:
        print("   ⏱️ Timeout — le serveur n'a pas répondu à temps.")

    except requests.exceptions.HTTPError as e:
        print(f"   ❌ Erreur HTTP : {e}")
        try:
            print(f"   Réponse serveur : {response.text}")
        except Exception:
            pass

    except KeyboardInterrupt:
        raise

    except Exception as e:
        print(f"   ❌ Erreur : {e}")


def main():
    parser = argparse.ArgumentParser(description="Simulateur SmartWatch IoT")

    parser.add_argument(
        "--url",
        default="http://localhost:8000/iot/data",
        help="URL de l'API IoT",
    )

    parser.add_argument(
        "--patient",
        default="patient_001",
        help="ID du patient",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Intervalle en secondes entre deux envois",
    )

    parser.add_argument(
        "--mode",
        choices=["normal", "anomaly", "random"],
        default="random",
        help="Mode de simulation",
    )

    args = parser.parse_args()

    print("\n⌚ SmartWatch Simulator démarré")
    print(f"   Patient   : {args.patient}")
    print(f"   API URL   : {args.url}")
    print(f"   Intervalle: {args.interval}s ({args.interval // 60} min)")
    print(f"   Mode      : {args.mode}")
    print("   Ctrl+C pour arrêter\n")

    try:
        while True:
            send_data(args.url, args.patient, args.mode)
            print(f"\n⏳ Prochain envoi dans {args.interval}s...")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n🛑 SmartWatch Simulator arrêté par l'utilisateur.")


if __name__ == "__main__":
    main()
