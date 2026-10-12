export interface BubblePosition {
    left: number;
    top: number;
}

export function scatterBubbles(
    count: number,
    bubbleSizePercent: number,
    minGapPercent = 8,
    maxAttempts = 200
): BubblePosition[] {
    const positions: BubblePosition[] = [];
    const half = bubbleSizePercent / 2;

    for (let i = 0; i < count; i++){
        let placed = false;

        for (let attempt = 0; attempt < maxAttempts && !placed; attempt++) {
            const candidate: BubblePosition = {
                left: half + Math.random() * (100 - bubbleSizePercent),
                top: half + Math.random() * (100 - bubbleSizePercent),
            };

            const overlaps = positions.some((pos) => {
                const dx = pos.left - candidate.left;
                const dy = pos.top - candidate.top;
                const distance = Math.sqrt(dx * dx + dy * dy);
                return distance < bubbleSizePercent + minGapPercent;
            });

            if (!overlaps) {
                positions.push(candidate);
                placed = true;
            }
        }

        if (!placed) {
            positions.push({
                left: half + Math.random() * (100 - bubbleSizePercent),
                top: half + Math.random() * (100 - bubbleSizePercent),
            });
        }
    }
    return positions;
}