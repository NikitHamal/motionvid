export interface Keyframe { t: number; v: number; ease?: string }
export interface Element { id: string; kind?: string; color?: string; tracks?: Record<string, Keyframe[]>; [k: string]: unknown }
export interface Timeline { fps: number; duration: number; width: number; height: number; bg?: string; elements: Element[]; cuts: unknown[]; sfx: unknown[] }
export interface Cue { t: number; role: string; dur: number; gain_db: number; pan: number; why: string }
export const EASES: Record<string, (u: number) => number>;
export function val(kfs: Keyframe[] | undefined, t: number): number | null;
export function drawFrame(ctx: CanvasRenderingContext2D, tl: Timeline, t: number, k?: number): void;
