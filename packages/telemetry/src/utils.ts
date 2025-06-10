import { trace, context, SpanStatusCode } from '@opentelemetry/api';
import { Span } from '@opentelemetry/api';

export interface TelemetryContext {
    span: Span;
    attributes: Record<string, string>;
}

export function createSpan(
    name: string,
    attributes: Record<string, string> = {}
): TelemetryContext {
    const tracer = trace.getTracer('fin-observability');
    const span = tracer.startSpan(name, {
        attributes: {
            ...attributes,
            'component': 'fin-observability',
        },
    });

    return {
        span,
        attributes,
    };
}

export function withSpan<T>(
    name: string,
    fn: (context: TelemetryContext) => Promise<T>,
    attributes: Record<string, string> = {}
): Promise<T> {
    const { span } = createSpan(name, attributes);
    const ctx = trace.setSpan(context.active(), span);

    return context.with(ctx, async () => {
        try {
            const result = await fn({ span, attributes });
            span.setStatus({ code: SpanStatusCode.OK });
            return result;
        } catch (error) {
            span.setStatus({
                code: SpanStatusCode.ERROR,
                message: error instanceof Error ? error.message : 'Unknown error',
            });
            throw error;
        } finally {
            span.end();
        }
    });
}

export function addEvent(
    span: Span,
    name: string,
    attributes: Record<string, string> = {}
): void {
    span.addEvent(name, attributes);
}

export function setAttributes(
    span: Span,
    attributes: Record<string, string>
): void {
    span.setAttributes(attributes);
}

export function recordException(
    span: Span,
    error: Error,
    attributes: Record<string, string> = {}
): void {
    span.recordException(error, attributes);
    span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
    });
} 