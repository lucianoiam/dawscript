// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

import java.util.List;
import java.util.Map;

public interface Controller
{
    Map<String,Object> get_config();

    void on_script_start();

    void on_script_stop();

    void on_project_load();

    void host_callback(List<byte[]> midi);
}
