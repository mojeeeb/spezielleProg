import os
import json
import time
import requests
import logging
from kubernetes import client, config

logging.basicConfig(level=logging.INFO)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://hooks.ferdous.work/webhook/def3c366-c5ca-45ab-ae01-8d6befd8ef00http://localhost:5678/webhook/22e3bd48-0301-4ecd-9493-d8eff6678856")
SCAN_FILE = "trivy-results.json"
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))

def load_scan_result(path):
    try:
        with open(path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        logging.error(f"Fehler beim Laden der Datei: {e}")
        return None
    
def monitor_kubernetes():
    """Monitor Kubernetes for issues"""
    try:
        # Load kube config
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        v1 = client.CoreV1Api()
        
        # Check for pods not in Running state
        pods = v1.list_namespaced_pod(namespace="smartops")
        issues = []
        
        for pod in pods.items:
            if pod.status.phase != "Running":
                issues.append({
                    "pod": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "reason": pod.status.reason or "Unknown"
                })
        
        if issues:
            # Determine severity based on number of issues
            severity = "LOW"
            if len(issues) > 5:
                severity = "CRITICAL"
            elif len(issues) > 3:
                severity = "HIGH"
            elif len(issues) > 1:
                severity = "MEDIUM"
            
            # Create summary
            summary = f"Found {len(issues)} pod issues in Kubernetes cluster:\n"
            for issue in issues[:3]:  # Show only first 3 issues
                summary += f"• Pod {issue['pod']} is in {issue['status']} state\n"
            
            if len(issues) > 3:
                summary += f"• ...and {len(issues) - 3} more issues\n"
    
    except Exception as e:
        print(f"Error monitoring Kubernetes: {str(e)}")

def send_to_n8n(payload):
    try:
        res = requests.post(N8N_WEBHOOK_URL, json=payload)
        logging.info(f"n8n Antwort: {res.status_code} - {res.text}")
    except Exception as e:
        logging.error(f"Fehler beim Senden an n8n: {e}")

def parse_trivy_results(results_file):
    """Parse Trivy scan results"""
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        vulnerabilities = []
        for result in data.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                vulnerabilities.append({
                    "VulnerabilityID": vuln.get("VulnerabilityID"),
                    "PkgName": vuln.get("PkgName"),
                    "Severity": vuln.get("Severity"),
                    "Title": vuln.get("Title"),
                    "Description": vuln.get("Description")
                })
        
        return vulnerabilities
    except Exception as e:
        return [{"Error": f"Failed to parse Trivy results: {str(e)}"}]

def main():
    while True:
        try:
            logging.info("🔍 Scandaten werden geladen...")
            # Check for new Trivy results
            monitor_kubernetes()
            if os.path.exists("/data/trivy-results.json"):
                vulnerabilities = parse_trivy_results("/data/trivy-results.json")
                send_to_n8n(vulnerabilities)
            else:
                logging.warning("Kein gültiges Ergebnis gefunden.")
            time.sleep(SCAN_INTERVAL)
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(60)
if __name__ == "__main__":
    main()