from collections import deque
from statistics import mean

OCCUPIED_THRESHOLD = 15
HIGH_PRESSURE_THRESHOLD = 110
MIN_REGION_PIXELS = 10


def neighbors(r, c, rows, cols):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            yield nr, nc


def connected_regions(matrix, threshold):
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    visited = [[False] * cols for _ in range(rows)]
    regions = []

    for r in range(rows):
        for c in range(cols):
            if visited[r][c] or matrix[r][c] <= threshold:
                continue
            q = deque([(r, c)])
            visited[r][c] = True
            coords = []
            values = []
            while q:
                cr, cc = q.popleft()
                coords.append((cr, cc))
                values.append(matrix[cr][cc])
                for nr, nc in neighbors(cr, cc, rows, cols):
                    if not visited[nr][nc] and matrix[nr][nc] > threshold:
                        visited[nr][nc] = True
                        q.append((nr, nc))
            regions.append({
                'coords': coords,
                'size': len(coords),
                'max_value': max(values),
                'avg_value': round(mean(values), 2),
                'bbox': {
                    'min_row': min(r for r, _ in coords),
                    'max_row': max(r for r, _ in coords),
                    'min_col': min(c for _, c in coords),
                    'max_col': max(c for _, c in coords),
                },
            })
    return regions


def compute_frame_metrics(matrix):
    flat = [value for row in matrix for value in row]
    occupied_pixels = sum(1 for value in flat if value > OCCUPIED_THRESHOLD)
    contact_area_percent = round((occupied_pixels / len(flat)) * 100, 2) if flat else 0
    occupied_regions = [r for r in connected_regions(matrix, OCCUPIED_THRESHOLD) if r['size'] >= MIN_REGION_PIXELS]
    ppi = max((r['max_value'] for r in occupied_regions), default=0)
    high_regions = [r for r in connected_regions(matrix, HIGH_PRESSURE_THRESHOLD) if r['size'] >= MIN_REGION_PIXELS]
    flagged = bool(high_regions)
    max_pressure = max(flat) if flat else 0
    summary = build_plain_english_summary(ppi, contact_area_percent, high_regions)
    return {
        'peak_pressure_index': ppi,
        'contact_area_percent': contact_area_percent,
        'occupied_pixels': occupied_pixels,
        'max_pressure': max_pressure,
        'high_pressure_regions': high_regions,
        'flagged_for_review': flagged,
        'plain_english_summary': summary,
    }


def build_plain_english_summary(ppi, contact_area_percent, high_regions):
    pressure_text = 'Pressure looks low and spread out.'
    if ppi >= HIGH_PRESSURE_THRESHOLD:
        pressure_text = 'There are strong pressure points that may need a position change.'
    elif ppi >= 70:
        pressure_text = 'Pressure is moderate, so it is worth keeping an eye on.'

    coverage_text = 'Only a small part of the mat is in contact.'
    if contact_area_percent >= 40:
        coverage_text = 'A large part of the mat is in contact with the body.'
    elif contact_area_percent >= 20:
        coverage_text = 'A moderate area of the mat is in contact.'

    risk_text = 'No high-risk pressure cluster was detected.'
    if high_regions:
        risk_text = f'{len(high_regions)} high-pressure region(s) were detected and flagged for review.'

    return f'{pressure_text} {coverage_text} {risk_text}'
