import type { ClientRead, Envelope, ClientProblem } from "../wire/generated";
import type { WireFailure } from "../wire/json";

export type ReadResponse<Payload> = Omit<ClientRead, "envelope"> & {
    readonly envelope: Omit<Envelope, "data"> & { readonly data: Payload };
};

export interface PreservedFailure {
    readonly request_id: string;
    readonly archive_id: string | null;
    readonly config_fingerprint: string | null;
    readonly command: string;
    readonly exit_code: number;
    readonly errors: Envelope["errors"];
    readonly warnings: Envelope["warnings"];
    readonly run_id: Envelope["run_id"];
    readonly started_at: Envelope["started_at"];
    readonly completed_at: Envelope["completed_at"];
    readonly outcome: Envelope["outcome"];
    readonly schema_version: Envelope["schema_version"];
}

export type ReadResult<Success, Failure> =
    | {
          readonly kind: "success";
          readonly response: ReadResponse<Success>;
          readonly payload: Success;
      }
    | {
          readonly kind: "domain_failure";
          readonly response: ReadResponse<Failure>;
          readonly payload: Failure;
      }
    | {
          readonly kind: "api_problem";
          readonly status: number;
          readonly problem: ClientProblem;
      }
    | {
          readonly kind: "protocol_failure";
          readonly reason: WireFailure;
          readonly preserved?: PreservedFailure;
      }
    | {
          readonly kind: "transport_failure";
          readonly reason: "network" | "timeout";
      }
    | { readonly kind: "aborted" };

export interface ReadOptions {
    readonly signal?: AbortSignal;
    /** A caller may lower the route's existing response ceiling, never raise it. */
    readonly responseByteLimit?: number;
}
