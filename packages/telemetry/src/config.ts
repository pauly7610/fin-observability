import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources';
import {
    ATTR_SERVICE_NAME,
    ATTR_SERVICE_VERSION,
    SEMRESATTRS_DEPLOYMENT_ENVIRONMENT,
} from '@opentelemetry/semantic-conventions';

export interface TelemetryConfig {
    serviceName: string;
    endpoint: string;
    environment: string;
    version: string;
}

export function initializeTelemetry(config: TelemetryConfig) {
    const traceExporter = new OTLPTraceExporter({
        url: `${config.endpoint}/v1/traces`,
    });

    const sdk = new NodeSDK({
        resource: resourceFromAttributes({
            [ATTR_SERVICE_NAME]: config.serviceName,
            [ATTR_SERVICE_VERSION]: config.version,
            [SEMRESATTRS_DEPLOYMENT_ENVIRONMENT]: config.environment,
        }),
        traceExporter,
        instrumentations: [getNodeAutoInstrumentations()],
    });

    // Initialize the SDK and register with the OpenTelemetry API
    try {
        sdk.start();
        console.log('Tracing initialized');
    } catch (error: unknown) {
        console.log('Error initializing tracing', error);
    }

    // Gracefully shut down the SDK on process exit
    process.on('SIGTERM', () => {
        sdk.shutdown()
            .then(() => console.log('Tracing terminated'))
            .catch((error: unknown) => console.log('Error terminating tracing', error))
            .finally(() => process.exit(0));
    });

    return sdk;
}

// Default configuration
export const defaultConfig: TelemetryConfig = {
    serviceName: 'fin-observability',
    endpoint: 'http://localhost:4318',
    environment: 'development',
    version: '0.1.0',
}; 