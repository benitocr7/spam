import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib

# ===============================
# 1. CARGAR DATASET
# ===============================
df = pd.read_csv(
    "spam.csv",
    sep=";",
    header=None,
    names=["label", "mensaje"],
    engine="python",
    on_bad_lines="skip"
)

print("Dataset cargado:", df.shape)

# ===============================
# 2. LIMPIEZA DE DATOS
# ===============================
# Eliminar filas vacías
df = df.dropna()

# Asegurar texto
df["mensaje"] = df["mensaje"].astype(str)

# Normalizar labels
df["label"] = df["label"].astype(str).str.lower().str.strip()

# Convertir labels a binario
# Todo lo que contenga "spam" → 1
# El resto → 0
df["label"] = df["label"].apply(lambda x: 1 if "spam" in x else 0)

print("Distribución de clases:")
print(df["label"].value_counts())
print("Total filas finales:", len(df))

# VERIFICACIÓN CRÍTICA
if len(df) == 0:
    raise ValueError("❌ El dataset quedó vacío después de la limpieza")

# ===============================
# 3. VARIABLES
# ===============================
X = df["mensaje"]
y = df["label"]

# ===============================
# 4. TRAIN / TEST SPLIT
# ===============================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ===============================
# 5. MODELO DE IA
# ===============================
modelo = Pipeline([
    ("tfidf", TfidfVectorizer(stop_words="english")),
    ("clf", MultinomialNB())
])

# ===============================
# 6. ENTRENAMIENTO
# ===============================
modelo.fit(X_train, y_train)

# ===============================
# 7. GUARDAR MODELO
# ===============================
joblib.dump(modelo, "modelo_spam.pkl")

print("✅ MODELO ENTRENADO Y GUARDADO COMO modelo_spam.pkl")
