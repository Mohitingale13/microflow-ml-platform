import io
from dataclasses import dataclass

import pandas as pd


@dataclass
class ValidationResult:
    valid: bool
    error: str | None = None


def validate_csv_content(content: bytes) -> ValidationResult:
    if not content:
        return ValidationResult(valid=False, error="File is empty")

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(
                io.BytesIO(content),
                encoding=encoding,
                nrows=5,
                on_bad_lines="skip",
            )

            if df.empty:
                return ValidationResult(valid=False, error="CSV contains no data rows")

            if len(df.columns) == 0:
                return ValidationResult(valid=False, error="CSV has no columns")

            all_unnamed = all(
                str(col).startswith("Unnamed:") for col in df.columns
            )
            if all_unnamed:
                return ValidationResult(
                    valid=False,
                    error="CSV is missing a proper header row",
                )

            return ValidationResult(valid=True)

        except pd.errors.EmptyDataError:
            return ValidationResult(valid=False, error="CSV contains no data")

        except pd.errors.ParserError as exc:
            return ValidationResult(valid=False, error=f"Malformed CSV: {exc}")

        except UnicodeDecodeError:
            continue

    return ValidationResult(
        valid=False,
        error="Unsupported file encoding — only UTF-8 and Latin-1 are accepted",
    )
