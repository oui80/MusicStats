#!/usr/bin/env python3
"""
Extraction de features audio + clustering des musiques téléchargées.

Entrée par défaut : music_downloads/
Sorties par défaut :
- music_features.csv
- music_clusters.csv
- music_cluster_summary.csv
- music_clusters.png

Installation :
    pip install -r requirements-audio.txt

Exemples :
    py cluster_music.py
    py cluster_music.py --clusters 6
    py cluster_music.py --auto-k
    py cluster_music.py --input-dir music_downloads --annotate
    py cluster_music.py --ffmpeg-path "C:\\chemin\\vers\\ffmpeg.exe"
"""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import tempfile
from pathlib import Path

import librosa
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


AUDIO_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".webm",
    ".opus",
    ".ogg",
    ".wav",
    ".flac",
    ".aac",
}


def find_audio_files(input_dir: Path) -> list[Path]:
    """Retourne les fichiers audio du dossier, en ignorant les JSON yt-dlp."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable : {input_dir}")

    files = [
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]

    return sorted(files, key=lambda p: p.name.lower())


def safe_float(value) -> float:
    """Convertit proprement les valeurs numpy/librosa en float simple."""
    try:
        if isinstance(value, np.ndarray):
            return float(np.nanmean(value))
        return float(value)
    except Exception:
        return float("nan")


def find_ffmpeg(ffmpeg_path: str | None = None) -> str | None:
    """Trouve ffmpeg, y compris dans quelques chemins Windows courants."""
    if ffmpeg_path:
        explicit = Path(ffmpeg_path)
        if explicit.exists():
            return str(explicit)
        found = shutil.which(ffmpeg_path)
        if found:
            return found
        return None

    found = shutil.which("ffmpeg")
    if found:
        return found

    candidates = []

    local_app_data = Path.home() / "AppData" / "Local"
    winget_packages = local_app_data / "Microsoft" / "WinGet" / "Packages"
    if winget_packages.exists():
        candidates.extend(winget_packages.glob("Gyan.FFmpeg*/*/bin/ffmpeg.exe"))
        candidates.extend(winget_packages.glob("Gyan.FFmpeg*/ffmpeg*/bin/ffmpeg.exe"))
        candidates.extend(winget_packages.glob("Gyan.FFmpeg*/bin/ffmpeg.exe"))

    candidates.extend(Path("C:/ffmpeg/bin").glob("ffmpeg.exe"))
    candidates.extend(Path("C:/Program Files").glob("**/ffmpeg.exe"))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def convert_with_ffmpeg(
    audio_path: Path,
    *,
    ffmpeg_bin: str,
    sample_seconds: float,
    sr: int,
    temp_dir: Path,
) -> Path:
    """Convertit un fichier audio en WAV temporaire lisible par librosa."""
    wav_path = temp_dir / f"{audio_path.stem}.wav"

    cmd = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
    ]

    if sample_seconds > 0:
        cmd.extend(["-t", str(sample_seconds)])

    cmd.extend(
        [
            "-i",
            str(audio_path),
            "-ac",
            "1",
            "-ar",
            str(sr),
            str(wav_path),
        ]
    )

    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0 or not wav_path.exists():
        message = (result.stderr or result.stdout or "erreur ffmpeg inconnue").strip()
        raise RuntimeError(f"ffmpeg n'a pas pu convertir le fichier : {message}")

    return wav_path


def load_audio(audio_path: Path, sample_seconds: float, sr: int, ffmpeg_bin: str | None) -> tuple[np.ndarray, int]:
    """
    Charge un fichier audio.

    Stratégie :
    1. essai direct avec librosa ;
    2. si échec, conversion WAV temporaire via ffmpeg ;
    3. chargement du WAV par librosa.
    """
    try:
        return librosa.load(
            str(audio_path),
            sr=sr,
            mono=True,
            duration=sample_seconds if sample_seconds > 0 else None,
        )
    except Exception as first_error:
        if not ffmpeg_bin:
            raise RuntimeError(
                "librosa n'a pas pu lire ce fichier et ffmpeg est introuvable. "
                "Ferme/réouvre le terminal après l'installation de ffmpeg, ou passe --ffmpeg-path. "
                f"Erreur initiale : {type(first_error).__name__}: {first_error!r}"
            ) from first_error

        with tempfile.TemporaryDirectory(prefix="musicstats_audio_") as tmp:
            temp_dir = Path(tmp)
            wav_path = convert_with_ffmpeg(
                audio_path,
                ffmpeg_bin=ffmpeg_bin,
                sample_seconds=sample_seconds,
                sr=sr,
                temp_dir=temp_dir,
            )
            return librosa.load(str(wav_path), sr=sr, mono=True)


def extract_features(audio_path: Path, sample_seconds: float, sr: int, ffmpeg_bin: str | None) -> dict:
    """
    Extrait un petit jeu de features robustes.

    On charge seulement les N premières secondes pour garder un script rapide.
    Les features sont volontairement simples : tempo, énergie, spectre, chroma, MFCC.
    """
    y, sr = load_audio(audio_path, sample_seconds=sample_seconds, sr=sr, ffmpeg_bin=ffmpeg_bin)

    if y.size == 0:
        raise ValueError("audio vide ou illisible")

    duration = librosa.get_duration(y=y, sr=sr)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    rms = librosa.feature.rms(y=y)
    zcr = librosa.feature.zero_crossing_rate(y)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    flatness = librosa.feature.spectral_flatness(y=y)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    features = {
        "file": str(audio_path),
        "name": audio_path.stem,
        "duration_sec": safe_float(duration),
        "tempo_bpm": safe_float(tempo),
        "rms_mean": safe_float(np.mean(rms)),
        "rms_std": safe_float(np.std(rms)),
        "zcr_mean": safe_float(np.mean(zcr)),
        "zcr_std": safe_float(np.std(zcr)),
        "spectral_centroid_mean": safe_float(np.mean(centroid)),
        "spectral_centroid_std": safe_float(np.std(centroid)),
        "spectral_bandwidth_mean": safe_float(np.mean(bandwidth)),
        "spectral_bandwidth_std": safe_float(np.std(bandwidth)),
        "spectral_rolloff_mean": safe_float(np.mean(rolloff)),
        "spectral_rolloff_std": safe_float(np.std(rolloff)),
        "spectral_flatness_mean": safe_float(np.mean(flatness)),
        "spectral_flatness_std": safe_float(np.std(flatness)),
        "chroma_mean": safe_float(np.mean(chroma)),
        "chroma_std": safe_float(np.std(chroma)),
    }

    for i in range(mfcc.shape[0]):
        features[f"mfcc_{i + 1:02d}_mean"] = safe_float(np.mean(mfcc[i]))
        features[f"mfcc_{i + 1:02d}_std"] = safe_float(np.std(mfcc[i]))

    return features


def choose_k_auto(x_scaled: np.ndarray, max_k: int) -> int:
    """Choisit k par silhouette score."""
    n_samples = x_scaled.shape[0]

    if n_samples < 3:
        return 1

    upper = min(max_k, n_samples - 1)
    if upper < 2:
        return 1

    best_k = 2
    best_score = -1.0

    for k in range(2, upper + 1):
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(x_scaled)
        score = silhouette_score(x_scaled, labels)

        if score > best_score:
            best_score = score
            best_k = k

    print(f"k automatique retenu : {best_k} | silhouette={best_score:.3f}")
    return best_k


def cluster_features(df: pd.DataFrame, clusters: int, auto_k: bool, max_k: int) -> tuple[pd.DataFrame, PCA, np.ndarray]:
    """Standardise les features, applique KMeans, puis projette en 2D avec PCA."""
    feature_cols = [
        col
        for col in df.columns
        if col not in {"file", "name"} and pd.api.types.is_numeric_dtype(df[col])
    ]

    if not feature_cols:
        raise ValueError("Aucune feature numérique disponible.")

    x = df[feature_cols].replace([np.inf, -np.inf], np.nan)
    x = x.fillna(x.median(numeric_only=True))
    x = x.fillna(0)

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    if auto_k:
        k = choose_k_auto(x_scaled, max_k=max_k)
    else:
        k = max(1, min(clusters, len(df)))

    if k == 1:
        labels = np.zeros(len(df), dtype=int)
    else:
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(x_scaled)

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(x_scaled)

    result = df.copy()
    result["cluster"] = labels
    result["x"] = coords[:, 0]
    result["y"] = coords[:, 1]

    return result, pca, x_scaled


def plot_clusters(df: pd.DataFrame, output_png: Path, annotate: bool) -> None:
    """Génère le graphe 2D des clusters."""
    plt.figure(figsize=(13, 8))

    scatter = plt.scatter(
        df["x"],
        df["y"],
        c=df["cluster"],
        cmap="tab10",
        s=70,
        alpha=0.85,
        edgecolors="black",
        linewidths=0.4,
    )

    if annotate:
        for _, row in df.iterrows():
            label = str(row["name"])
            if len(label) > 35:
                label = label[:32] + "..."
            plt.annotate(label, (row["x"], row["y"]), fontsize=7, alpha=0.75)

    plt.title("Clustering des musiques à partir des features audio")
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.grid(True, alpha=0.25)

    legend = plt.legend(*scatter.legend_elements(), title="Cluster", loc="best")
    plt.gca().add_artist(legend)

    plt.tight_layout()
    plt.savefig(output_png, dpi=180)
    plt.close()


def export_cluster_summary(df: pd.DataFrame, output_csv: Path) -> None:
    """Exporte un résumé lisible par cluster."""
    rows = []

    for cluster_id, group in df.groupby("cluster"):
        rows.append(
            {
                "cluster": int(cluster_id),
                "count": len(group),
                "avg_tempo_bpm": round(group["tempo_bpm"].mean(), 1),
                "avg_rms": round(group["rms_mean"].mean(), 4),
                "avg_spectral_centroid": round(group["spectral_centroid_mean"].mean(), 1),
                "examples": " | ".join(group["name"].head(8).tolist()),
            }
        )

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "cluster",
                "count",
                "avg_tempo_bpm",
                "avg_rms",
                "avg_spectral_centroid",
                "examples",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extraction de features audio et clustering des musiques téléchargées."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("music_downloads"),
        help="Dossier contenant les musiques téléchargées.",
    )
    parser.add_argument(
        "--output-prefix",
        default="music",
        help="Préfixe des fichiers de sortie.",
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=5,
        help="Nombre de clusters KMeans.",
    )
    parser.add_argument(
        "--auto-k",
        action="store_true",
        help="Choisit automatiquement le nombre de clusters par silhouette score.",
    )
    parser.add_argument(
        "--max-k",
        type=int,
        default=10,
        help="Nombre maximal de clusters testé avec --auto-k.",
    )
    parser.add_argument(
        "--sample-seconds",
        type=float,
        default=90.0,
        help="Nombre de secondes analysées par titre. 0 = titre complet.",
    )
    parser.add_argument(
        "--sr",
        type=int,
        default=22050,
        help="Fréquence d'échantillonnage utilisée par librosa.",
    )
    parser.add_argument(
        "--annotate",
        action="store_true",
        help="Affiche les noms des morceaux sur le graphe. Lisible surtout avec peu de titres.",
    )
    parser.add_argument(
        "--ffmpeg-path",
        default=None,
        help="Chemin optionnel vers ffmpeg.exe si le terminal ne trouve pas encore ffmpeg.",
    )

    args = parser.parse_args()

    audio_files = find_audio_files(args.input_dir)
    if not audio_files:
        raise FileNotFoundError(
            f"Aucun fichier audio trouvé dans {args.input_dir}. "
            "Lance d'abord download_music.py sans --dry-run."
        )

    ffmpeg_bin = find_ffmpeg(args.ffmpeg_path)
    if ffmpeg_bin:
        print(f"ffmpeg détecté : {ffmpeg_bin}")
    else:
        print(
            "ffmpeg non détecté. Le script essaiera la lecture directe avec librosa. "
            "Pour les .webm, ferme/réouvre PowerShell ou passe --ffmpeg-path."
        )

    print(f"{len(audio_files)} fichiers audio trouvés dans {args.input_dir}")

    features = []
    errors = []

    for index, audio_path in enumerate(audio_files, start=1):
        print(f"[{index}/{len(audio_files)}] Analyse : {audio_path.name}")
        try:
            features.append(
                extract_features(
                    audio_path=audio_path,
                    sample_seconds=args.sample_seconds,
                    sr=args.sr,
                    ffmpeg_bin=ffmpeg_bin,
                )
            )
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc!r}"
            print(f"  Erreur : {audio_path.name} | {error_message}")
            errors.append({"file": str(audio_path), "error": error_message})

    errors_csv = Path(f"{args.output_prefix}_feature_errors.csv")

    if not features:
        if errors:
            pd.DataFrame(errors).to_csv(errors_csv, index=False, encoding="utf-8-sig")
            raise RuntimeError(
                "Aucun fichier audio n'a pu être analysé. "
                f"Détails enregistrés dans : {errors_csv}. "
                "Ferme/réouvre PowerShell après l'installation de ffmpeg, puis relance."
            )
        raise RuntimeError("Aucun fichier audio n'a pu être analysé.")

    features_df = pd.DataFrame(features)

    features_csv = Path(f"{args.output_prefix}_features.csv")
    clusters_csv = Path(f"{args.output_prefix}_clusters.csv")
    summary_csv = Path(f"{args.output_prefix}_cluster_summary.csv")
    graph_png = Path(f"{args.output_prefix}_clusters.png")

    features_df.to_csv(features_csv, index=False, encoding="utf-8-sig")

    clustered_df, pca, _ = cluster_features(
        df=features_df,
        clusters=args.clusters,
        auto_k=args.auto_k,
        max_k=args.max_k,
    )

    clustered_df.to_csv(clusters_csv, index=False, encoding="utf-8-sig")
    export_cluster_summary(clustered_df, summary_csv)
    plot_clusters(clustered_df, graph_png, annotate=args.annotate)

    if errors:
        pd.DataFrame(errors).to_csv(errors_csv, index=False, encoding="utf-8-sig")

    explained = pca.explained_variance_ratio_
    print("\nTerminé.")
    print(f"Features : {features_csv}")
    print(f"Clusters : {clusters_csv}")
    print(f"Résumé clusters : {summary_csv}")
    print(f"Graphe : {graph_png}")
    print(f"Variance PCA expliquée : PC1={explained[0]:.2%}, PC2={explained[1]:.2%}")

    if errors:
        print(f"Fichiers non analysés : {len(errors)} | détails : {errors_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
