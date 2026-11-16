"""Pure framing solver: no Blender dependency, no render side effects."""
def solve_framing(width_fraction,height_fraction,min_height=.72,max_height=.93,max_width=.95):
    if not (0 < width_fraction <= 1 and 0 < height_fraction <= 1):
        return {"status":"BLOCKED_INVALID_INPUT"}
    low=min_height/height_fraction
    high=min(max_height/height_fraction,max_width/width_fraction)
    if low>high:
        return {"status":"BLOCKED_INFEASIBLE","minimum_zoom":round(low,6),"maximum_zoom":round(high,6)}
    # Minimize unnecessary zoom and avoid clipping; no arbitrary 83% target.
    zoom=low
    return {"status":"FEASIBLE","zoom":round(zoom,6),"predicted_height":round(height_fraction*zoom,6),"predicted_width":round(width_fraction*zoom,6)}
