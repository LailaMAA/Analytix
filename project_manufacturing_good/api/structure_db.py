from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Full Enterprise Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./Companyx_database.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 1. CORE DIMENSIONS (Real Data Sources)
# ==========================================

class DimRegion(Base):
    __tablename__ = "DIM_REGION"
    region_id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String, index=True)
    climate = Column(String)

class DimFailureType(Base):
    __tablename__ = "DIM_FAILURE_TYPE"
    failure_type_id = Column(Integer, primary_key=True, index=True)
    failure_name = Column(String)

class DimPart(Base):
    __tablename__ = "DIM_PART"
    part_id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String)
    category = Column(String)
    unit_cost = Column(Float)
    criticality_level = Column(String)

# ==========================================
# 2. SYNTHETIC BUSINESS DIMENSIONS
# ==========================================

class DimCustomer(Base):
    __tablename__ = "DIM_CUSTOMER"
    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    email = Column(String)
    phone = Column(String)
    
    vehicles = relationship("DimVehicle", back_populates="customer")

class DimDealer(Base):
    __tablename__ = "DIM_DEALER"
    dealer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    region_id = Column(Integer, ForeignKey("DIM_REGION.region_id"))
    technician_count = Column(Integer)
    daily_capacity = Column(Integer)
    
    region = relationship("DimRegion")

# ==========================================
# 3. HYBRID DIMENSIONS (Linked)
# ==========================================

class DimVehicle(Base):
    __tablename__ = "DIM_VEHICLE"
    vehicle_id = Column(Integer, primary_key=True, index=True)
    original_vehicle_id = Column(String, unique=True, index=True)
    engine_model = Column(String)
    vehicle_type = Column(String)
    vehicle_age = Column(Float)
    under_warranty = Column(String)
    service_start_date = Column(String)
    
    customer_id = Column(Integer, ForeignKey("DIM_CUSTOMER.customer_id"), nullable=True)
    customer = relationship("DimCustomer", back_populates="vehicles")

class DimDate(Base):
    __tablename__ = "DIM_DATE"
    date_id = Column(Integer, primary_key=True, index=True)
    date_iso = Column(String, unique=True)
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)

# ==========================================
# 4. FACT TABLES
# ==========================================

class FactVehicleFailure(Base):
    __tablename__ = "FACT_VEHICLE_FAILURE"
    fact_id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("DIM_VEHICLE.vehicle_id"))
    region_id = Column(Integer, ForeignKey("DIM_REGION.region_id"))
    failure_type_id = Column(Integer, ForeignKey("DIM_FAILURE_TYPE.failure_type_id"))
    part_id = Column(Integer, ForeignKey("DIM_PART.part_id"))
    time_id = Column(Integer, ForeignKey("DIM_DATE.date_id"), nullable=True)
    total_mileage = Column(Float)
    engine_rpm = Column(Float)
    engine_temperature = Column(Float)
    oil_pressure = Column(Float)
    days_before_failure = Column(Integer)
    last_maintenance_date = Column(String)

    vehicle = relationship("DimVehicle")
    region = relationship("DimRegion")
    failure_type = relationship("DimFailureType")
    part = relationship("DimPart")

class FactHRForecast(Base):
    __tablename__ = "FACT_HR_FORECAST"
    hr_event_id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("DIM_REGION.region_id"))
    time_id = Column(Integer, ForeignKey("DIM_DATE.date_id"))
    required_technicians = Column(Integer)
    availability_rate = Column(Float)

class FactInventoryForecast(Base):
    __tablename__ = "FACT_INVENTORY_FORECAST"
    inventory_event_id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("DIM_PART.part_id"))
    time_id = Column(Integer, ForeignKey("DIM_DATE.date_id"))
    predicted_shortage = Column(Integer)
    reorder_probability = Column(Float)

class FactInvestmentForecast(Base):
    __tablename__ = "FACT_INVESTMENT_FORECAST"
    investment_event_id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("DIM_REGION.region_id"))
    time_id = Column(Integer, ForeignKey("DIM_DATE.date_id"))
    estimated_cost = Column(Float)
    roi_prediction = Column(Float)

class FactWarrantyImpact(Base):
    __tablename__ = "FACT_WARRANTY_IMPACT"
    warranty_event_id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("DIM_VEHICLE.vehicle_id"))
    time_id = Column(Integer, ForeignKey("DIM_DATE.date_id"))
    warranty_impact_score = Column(Float)
    failure_confirmed = Column(Integer)

class FactInventory(Base):
    __tablename__ = "FACT_INVENTORY"
    inventory_id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(Integer, ForeignKey("DIM_DEALER.dealer_id"))
    part_id = Column(Integer, ForeignKey("DIM_PART.part_id"))
    current_stock = Column(Integer)
    reorder_level = Column(Integer)
    last_restock_date = Column(String)
    
    dealer = relationship("DimDealer")
    part = relationship("DimPart")

class FactMaintenanceLog(Base):
    __tablename__ = "FACT_MAINTENANCE_LOG"
    log_id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("DIM_VEHICLE.vehicle_id"))
    dealer_id = Column(Integer, ForeignKey("DIM_DEALER.dealer_id"))
    date_iso = Column(String)
    description = Column(String)
    cost = Column(Float)
    
    vehicle = relationship("DimVehicle")
    dealer = relationship("DimDealer")

class FactPrediction(Base):
    """
    PREDICTION LOGS: Stores Snapshots of Inputs + AI Inference results.
    """
    __tablename__ = "FACT_PREDICTION"
    prediction_id = Column(Integer, primary_key=True, index=True)
    
    # Link to unique vehicle (Internal ID)
    vehicle_id = Column(Integer, ForeignKey("DIM_VEHICLE.vehicle_id"))
    prediction_date = Column(DateTime, default=datetime.utcnow)
    
    # --- SNAPSHOT INPUTS (Features used for prediction - Standardized English) ---
    engine_model = Column(String)      # was Model_moteur
    vehicle_age = Column(Float)       # was age_vehicule
    total_mileage = Column(Float)     # was kilometrage_total
    warranty = Column(String)         # was Garantie
    last_maintenance_date = Column(String) # was date_derniere_maintenance
    service_start_date = Column(String)    # was Date_mise_service
    
    # Données capteurs (Telemetry)
    engine_rpm = Column(Float)
    engine_load = Column(Float)
    engine_temperature = Column(Float)
    oil_temperature = Column(Float)
    oil_pressure = Column(Float)
    fuel_pressure = Column(Float)
    
    # Localisation et Contexte
    region = Column(String)
    city = Column(String)             # was ville
    defective_part = Column(String)   # was Piece_defectuee
    impacted_part = Column(String)    # was piece_impacte
    
    # --- OUTPUTS (AI Results) ---
    predicted_failure_type = Column(String)
    failure_probability = Column(Float)
    predicted_days_before_failure = Column(Integer)
    
    # Recommendation
    recommended_part_id = Column(Integer, ForeignKey("DIM_PART.part_id"), nullable=True)
    
    vehicle = relationship("DimVehicle")

class FactTrainingData(Base):
    """
    TRAINING DATASET: Denormalized table for Model Training (Single Source of Truth).
    """
    __tablename__ = "FACT_TRAINING_DATA"
    training_id = Column(Integer, primary_key=True, index=True)
    
    # Identifier
    vehicle_id = Column(String) # Original ID
    
    # Features (Standardized English)
    engine_model = Column(String)      # was Model_moteur
    vehicle_age = Column(Float)
    total_mileage = Column(Float)
    engine_rpm = Column(Float)
    engine_load = Column(Float)
    engine_temperature = Column(Float)
    oil_temperature = Column(Float)
    oil_pressure = Column(Float)
    fuel_pressure = Column(Float)
    last_maintenance_date = Column(String) # was date_derniere_maintenance
    warranty = Column(String)         # was Garantie
    service_start_date = Column(String)    # was Date_mise_service
    region = Column(String)
    city = Column(String)             # was ville
    
    # Target / Outcomes (Standardized English)
    failure_type = Column(String)     # was type_panne_moteur
    days_before_failure = Column(Integer) # was jours_avant_panne
    defective_part = Column(String)   # was Piece_defectuee
    impacted_part = Column(String)    # was piece_impacte

def init_enterprise_db():
    Base.metadata.create_all(bind=engine)
