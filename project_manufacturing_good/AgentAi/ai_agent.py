import pandas as pd
from datetime import datetime
import collections
import os
from AgentAi.llm_client import LLMClient

class MaintenanceAgent:
    def __init__(self, data: pd.DataFrame):
        """
        Initializes the agent with prediction data.
        :param data: DataFrame containing the FACT_PREDICTION table.
        """
        self.data = data
        self.today = datetime.now()
        self.llm_client = LLMClient()
        self.cache_dir = os.path.dirname(os.path.abspath(__file__))

    def detect_abnormal_patterns(self):
        """
        Detects abnormal patterns (e.g., regional concentrations).
        Returns a list of significant insights.
        """
        insights = []
        
        # 1. Regional concentration of failure types
        if 'region' in self.data.columns and 'predicted_failure_type' in self.data.columns:
            # Group by Region and Failure Type
            pattern_counts = self.data.groupby(['region', 'predicted_failure_type']).size().reset_index(name='count')
            
            # Simple anomaly detection: if a failure type in a region is > 20% of total failures in that region
            total_per_region = self.data.groupby('region').size()
            
            for index, row in pattern_counts.iterrows():
                region = row['region']
                count = row['count']
                total = total_per_region.get(region, 0)
                
                if total > 0 and (count / total) > 0.25: # Threshold for "abnormal"
                    percentage = int((count / total) * 100)
                    insights.append(f"Augmentation anormale de **{row['predicted_failure_type']}** détectée dans la région **{region}** ({percentage}% des pannes).")

        return insights

    def identify_critical_failures(self, days_horizon=30):
        """
        Identifies upcoming critical failures within a short-term horizon.
        """
        critical = self.data[
            (self.data['predicted_days_before_failure'] <= days_horizon) &
            (self.data['predicted_days_before_failure'] > 0)
        ]
        return critical

    def predict_spare_parts_demand(self, days_horizon=30):
        """
        Anticipates spare parts demand based on predicted failures.
        """
        upcoming = self.identify_critical_failures(days_horizon)
        if upcoming.empty:
            return pd.DataFrame()

        # Count occurrences of defective parts
        demand = upcoming['defective_part'].value_counts().reset_index()
        demand.columns = ['Nom de la Pièce', 'Demande Estimée']
        return demand

    def evaluate_business_impact(self, critical_failures):
        """
        Evaluates warranty cost exposure and operational risk.
        """
        impact = {
            'warranty_exposure_count': 0,
            'high_risk_regions': [],
            'urgent_actions': []
        }
        
        if critical_failures.empty:
            return impact

        # Warranty Exposure
        if 'warranty' in critical_failures.columns:
            warranty_claims = critical_failures[critical_failures['warranty'] == True]
            impact['warranty_exposure_count'] = len(warranty_claims)
        
        # Operational Risk (Regional)
        if 'region' in critical_failures.columns:
            impact['high_risk_regions'] = critical_failures['region'].mode().tolist()

        return impact

    def generate_daily_briefing(self):
        """
        Generates a concise, executive-level markdown report.
        Uses LLM if available, otherwise falls back to template.
        CACHING: Returns cached file if available for today.
        """
        # 1. Check Cache
        date_str = self.today.strftime('%Y-%m-%d')
        cache_file = os.path.join(self.cache_dir, f"briefing_{date_str}.md")
        
        if os.path.exists(cache_file):
            print(f"[AGENT] (CACHE) Rapport trouve en cache : {cache_file}")
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()

        # Horizons
        short_term = 7
        medium_term = 30
        
        # Analysis
        critical_7d = self.identify_critical_failures(short_term)
        critical_30d = self.identify_critical_failures(medium_term)
        patterns = self.detect_abnormal_patterns()
        parts_demand = self.predict_spare_parts_demand(medium_term)
        impact_30d = self.evaluate_business_impact(critical_30d)
        
        avg_days = self.data['predicted_days_before_failure'].mean()
        
        # Prepare Data Context for LLM
        data_context = {
            'avg_days': f"{avg_days:.1f}",
            'patterns': patterns,
            'critical_failures': critical_7d[['vehicle_id', 'engine_model', 'predicted_failure_type', 'predicted_days_before_failure', 'warranty']].to_dict('records'),
            'parts_demand': parts_demand.head(5).to_dict('records') if not parts_demand.empty else [],
            'impact': impact_30d
        }

        # Construct Prompt
        prompt = f"""
        Tu es un Analyste de Maintenance Autonome expert.
        Ta tâche est de rédiger un briefing quotidien pour l'équipe exécutive et technique.
        Utilise les données fournies ci-dessous pour créer un rapport professionnel, clair et percutant en format Markdown.
        Écris en français.
        
        **Données du jour :**
        - Date : {self.today.strftime('%d/%m/%Y')}
        - Moyenne jours avant panne : {data_context.get('avg_days', 'N/A')}
        
        **1. Anomalies détectées :**
        {data_context.get('patterns', [])}
        
        **2. Pannes Critiques (7 prochains jours) :**
        {data_context.get('critical_failures', [])}
        
        **3. Prévisions de pièces (30 jours) :**
        {data_context.get('parts_demand', [])}
        
        **4. Impact Business :**
        {data_context.get('impact', {})}
        
        **Consignes de rédaction :**
        - Commence par un titre clair.
        - Fais un résumé exécutif en premier.
        - Utilise des emojis pour rendre la lecture fluide (⚠️ pour les risques, 📦 pour le stock, etc.).
        - Suggère des actions concrètes basées sur les données.
        - Sois précis mais concis.
        - Si aucune panne critique ou anomalie, mentionne que tout est nominal.
        """

        # Save to Cache (whether LLM or Fallback)
        final_report = ""
        
        # Try generating with LLM
        llm_report = self.llm_client.generate_report(prompt)
        if llm_report:
            final_report = llm_report
        else:    
            print("[AGENT] (WARN) Fallback to legacy report generation (LLM unavailable).")
            # Fallback Report Construction (Legacy Code)
            report_lines = []
            report_lines.append(f"# 🔍 Rapport d'Analyste de Maintenance Autonome (Mode Secours)")
            report_lines.append(f"**Date**: {self.today.strftime('%d/%m/%Y')}")
            report_lines.append("")
            
            # 1. Executive Summary & Patterns
            report_lines.append("## 1. Résumé Exécutif & Anomalies")
            if patterns:
                for p in patterns:
                    report_lines.append(f"- ⚠️ {p}")
            else:
                report_lines.append("- Aucun modèle régional anormal détecté aujourd'hui.")
                
            report_lines.append(f"- Moyenne de jours avant défaillance sur la flotte : **{avg_days:.1f} jours**.")
            report_lines.append("")

            # 2. Critical Upcoming Failures
            report_lines.append(f"## 2. Défaillances Critiques (Prochains {short_term} Jours)")
            if not critical_7d.empty:
                report_lines.append(f"> [!WARNING] **{len(critical_7d)} véhicules** devraient tomber en panne dans les prochains {short_term} jours.")
                
                # Show top 3 most urgent
                urgent = critical_7d.nsmallest(3, 'predicted_days_before_failure')
                for _, row in urgent.iterrows():
                    warranty_str = " (SOUS GARANTIE)" if row.get('warranty') == 'Oui' else ""
                    report_lines.append(f"- Véhicule `{row['vehicle_id']}` ({row.get('engine_model','N/A')}) : {row['predicted_failure_type']} dans **{row['predicted_days_before_failure']} jours**{warranty_str}.")
            else:
                report_lines.append(f"Aucune défaillance critique immédiate prévue dans les prochains {short_term} jours.")
            report_lines.append("")

            # 3. Supply Chain & Parts Demand
            report_lines.append(f"## 3. Analyses Logistiques (Prochains {medium_term} Jours)")
            if not parts_demand.empty:
                top_part = parts_demand.iloc[0]
                if top_part['Demande Estimée'] > 5: # Threshold
                     report_lines.append(f"- 📦 **Alerte Stock**: `{top_part['Nom de la Pièce']}` nécessitera **{top_part['Demande Estimée']} unités**. Révision du stock recommandée.")
                
                report_lines.append("| Nom de la Pièce | Demande Estimée (30j) |")
                report_lines.append("|---|---|")
                for _, row in parts_demand.head(5).iterrows():
                    report_lines.append(f"| {row['Nom de la Pièce']} | **{row['Demande Estimée']}** |")
            else:
                report_lines.append("Aucune demande significative de pièces prévue.")
            report_lines.append("")

            # 4. Business Impact & Recommendations
            report_lines.append("## 4. Impact Commercial & Actions Recommandées")
            report_lines.append(f"- **Risque Garantie**: {impact_30d['warranty_exposure_count']} pannes prévues sont sous garantie.")
            
            actions = []
            if impact_30d['warranty_exposure_count'] > 5:
                actions.append("Prioriser la maintenance préventive des véhicules sous garantie pour réduire les coûts.")
            
            if patterns:
                 actions.append("Enquêter sur les centres de services régionaux mentionnés pour des problèmes potentiels de qualité.")
                 
            if not parts_demand.empty and parts_demand.iloc[0]['Demande Estimée'] > 10:
                 actions.append(f"Augmenter immédiatement les commandes de stock pour {parts_demand.iloc[0]['Nom de la Pièce']}.")

            if actions:
                report_lines.append("### Actions Recommandées :")
                for action in actions:
                    report_lines.append(f"- ☑️ {action}")
            else:
                report_lines.append("Aucune action stratégique immédiate requise. Continuer la surveillance.")
                
            final_report = "\n".join(report_lines)

        # Write to cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(final_report)
            print(f"[AGENT] (CACHE) Nouveau rapport sauvegardé : {cache_file}")
        except Exception as e:
            print(f"[AGENT] (ERROR) Impossible de sauvegarder le cache : {e}")

        return final_report

    def dispatch_alert(self, content):
        """
        Simulates sending the alert to different business units.
        """
        print(f"\n[AGENT] (INFO) Diffusion du Briefing Quotidien aux Abonnés...")
        
        # In a real system, we would parse the content or use the structured data directly.
        # Here we simulate routing based on keywords in the report.
        
        # 1. Warranty Department
        if "[!WARNING]" in content or "Risque Garantie" in content:
            print("[AGENT] (ALERT) ALERTE envoyée au **Service Garantie** : Véhicules à haut risque identifiés.")
            
        # 2. Logistics / Supply Chain
        if "Alerte Stock" in content or "Analyses Logistiques" in content:
            print("[AGENT] (STOCK) COMMANDE DÉCLENCHÉE envoyée à la **Logistique** : Ajustement de stock recommandé.")
            
        # 3. Regional Operations
        if "Augmentation anormale" in content:
            print("[AGENT] (REGION) NOTIFICATION envoyée aux **Opérations Régionales** : Anomalie détectée.")
            
        print("[AGENT] (OK) Rapport livré au Tableau de Bord Exécutif via API (200 OK).")
