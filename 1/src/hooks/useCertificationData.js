import { useMemo } from "react";
import { processCertificationData } from "../utils/certificationUtils";

export function useCertificationData(certifications, branchFilter, criticalityFilter) {
  return useMemo(() => {
    return processCertificationData(certifications, branchFilter, criticalityFilter);
  }, [certifications, branchFilter, criticalityFilter]);
}